import sys
import os
import subprocess
import re
import shutil
from typing import Dict, List

def parse_args() -> Dict:
    """
    Parse command args
    """
    args = iter(sys.argv[1:])
    opts = {
        "frame_path": None,
        "keyframe_path": None,
        "output": None,
        "ebsynth": "ebsynth",
        "verbose": 0,
    }

    pos = 0
    try:
        while True:
            a = next(args)
            if a == "-o" or a == "--output":
                opts["output"] = next(args)
            elif a == "--ebsynth":
                opts["ebsynth"] = next(args)
            elif a == "-v":
                opts["verbose"] += 1
            else:
                if pos == 0:
                    opts["frame_path"]= a
                elif pos == 1:
                    opts["keyframe_path"] = a
                pos += 1
    except StopIteration:
        pass

    return opts


def frame_from_name(path: str) -> int:
    """
    Extract the frame number from filename
    """
    name, _ = os.path.splitext(os.path.basename(path))
    numbers = re.split(r"\D", name)
    return int(numbers[-1])
    

def output_path(output: str, n: int) -> str:
    """
    Format the output path for frame `n`
    """
    if output.find("{n}") >= 0:
        return output.replace("{n}", f"{n:05}")
    else:
        return f"{output}{n:05d}.png"


def render_frames(keyframe: str, frames: List[str], output: str, ebsynth: str, verbose: int):
    """
    Render multiple frames from a single keyframes by using the last frame as a new keyframe.
    """
    for i in range(1, len(frames)):
        guide = frames[i-1]
        frame = frames[i]

        # Sometimes the frame nubers start from 1 so frame #0 isn't available
        # for example
        if frame is None:
            continue

        n = frame_from_name(frame)


        if verbose > 0:
            print(f"Processing frame #{n} ({frame})")
        pass

        # Run the command
        out_path = output_path(output, frame_from_name(frame))
        args = [ebsynth, "-style", keyframe, "-guide", guide, frame, "-output", out_path]
        out = subprocess.run(args, capture_output=True)

        # If the command fails or verbose level > 1, print the command output
        if out.returncode != 0:
            print("Ebsynth returned a nonzero exit code:")
        if verbose >= 2 or out.returncode != 0:
            print(out.stdout.decode("utf-8"))

        keyframe = out_path


def run(frame_path: str, keyframe_path: str, output: str, ebsynth: str, verbose: int=0):
    # A list of keyframes and their positions, sorted in ascending order
    keyframes = []
    for root, _, files in os.walk(keyframe_path):
        for p in files:
            n = frame_from_name(p)
            path = os.path.join(root, p)
            keyframes.append((n, path))
    keyframes.sort(key=lambda a: a[0])
            
    # A list of frames in order
    frames = []
    for root, _, files in os.walk(frame_path):
        for p in files:
            n = frame_from_name(p)
            path = os.path.join(root, p)
            frames += [None] * max(0, n - len(frames) + 1)
            frames[n] = path

    # Render the frames nearest to each keyframe
    for i in range(len(keyframes)):
        keyframe = keyframes[i]
        n = keyframe[0]

        # Render frames before the keyframe
        if i > 0:
            prev = keyframes[i-1]
            l = n - prev[0] - 1
            segment = l - l // 2
            render_frames(keyframe[1], frames[n:n-segment-1:-1], output, ebsynth, verbose)
        else:
            render_frames(keyframe[1], frames[n::-1], output, ebsynth, verbose)

        # Render frames after the keyframe
        if i < len(keyframes) - 1:
            post = keyframes[i + 1]
            l = post[0] - n - 1
            segment = l // 2
            render_frames(keyframe[1], frames[n:n+segment+1], output, ebsynth, verbose)        
        else:
            render_frames(keyframe[1], frames[n:], output, ebsynth, verbose)

        # Copy the keyframe to the output
        out_path = output_path(output, n)
        shutil.copy(keyframe[1], out_path)


if __name__ == "__main__":
    run(**parse_args())
