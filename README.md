# Ebsynth-utils

## crop.py
Try to automatically crop areas outside of a greenscreen.

```
python3 crop.py <input> <output>
```

## ebsynth.py
Style an image sequence with keyframes using ebsynth.

```
python3 ebsynth.py <frames> <keyframes> [OPTIONS]
```
- `<frames>`
  Directory containing frames of the video.
- `<keyframes>`
  Directory containing keyframes.
- `-o` | `--output`
  The output directory. If the path contains `{n}`, the `{n}` is replaced by
  the frame number, otherwise `{n}.png` is appended.
- `--ebsynth`
  Path to the ebsynth executable to use.
- `-v`
  Add a level of verbosity. This flag may repeat.
