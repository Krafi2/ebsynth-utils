import sys
import os
import subprocess
import re
import shutil
from typing import Dict

def parse_args() -> Dict:
    args = iter(sys.argv[1:])
    opts = {
        "frames": None,
        "keyframes": None,
        "output": None,
        "reverse": False,
        "ebsynth": "ebsynth",
        "verbose": 0,
    }

    pos = 0
    try:
        while True:
            a = next(args)
            if a == "-o" or a == "--output":
                opts["output"] = next(args)
            elif a == "--reverse":
                opts["reverse"] = True
            elif a == "--ebsynth":
                opts["ebsynth"] = next(args)
            elif a == "-v":
                opts["verbose"] += 1
            else:
                if pos == 0:
                    opts["frames"]= a
                elif pos == 1:
                    opts["keyframes"] = a
                pos += 1
    except StopIteration:
        pass

    return opts


def frame_from_path(path: str) -> int:
    name, _ = os.path.splitext(os.path.basename(path))
    numbers = re.split(r"\D", name)
    return int(numbers[-1])
    

def output_path(output: str, n: int) -> str:
    if output.find("{n}") >= 0:
        return output.replace("{n}", f"{n:05}")
    else:
        return f"{output}{n:05d}.png"


def run(frames: str, keyframes: str, output: str, ebsynth: str, reverse: bool=False, verbose: int=0):
    # Maps frame nubers to keyframes
    key_map = {}
    for root, _, files in os.walk(keyframes):
        for p in files:
            n = frame_from_path(p)
            key_map[n] = os.path.join(root, p)

            
    for root, _, files in os.walk(frames):
        frame_files = [os.path.join(root, p) for p in files]
        frame_files.sort(key=frame_from_path, reverse=reverse)
        print(f"Starting at frame #{frame_from_path(frame_files[0])} ({frame_files[0]})")

        for i in range(len(frame_files)):
            frame = frame_files[i]
            n = frame_from_path(frame)

            if verbose > 0:
                print(f"Processing frame #{n} ({frame})")

            # Copy the keyframe to the output
            if n in key_map:
                out_path = output_path(output, n)
                shutil.copy(key_map[n], out_path)
            else:
                if i == 0:
                    print(f"Error: No guide for frame #{n} ({frame})")
                    print("Aborting")
                    return
                    
                guide = frame_files[i-1]
                n = frame_from_path(guide)

                keyframe = None
                if n in key_map:
                    keyframe = key_map[n]
                else:
                    keyframe = output_path(output, n)

                if keyframe is None:
                    print(f"Error: No keyframe for frame #{n} ({guide})")
                    print("Aborting")
                    return

                out_path = output_path(output, frame_from_path(frame))
                out = subprocess.run([ebsynth, "-style", keyframe, "-guide", guide, frame, "-output", out_path], capture_output=True)
                if verbose > 2 or out.returncode != 0:
                    print(out.stdout)
        


if __name__ == "__main__":
    run(**parse_args())
