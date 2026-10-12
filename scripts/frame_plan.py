"""Integer-frame half-open interval intersections before converting to seconds."""
from __future__ import annotations
import argparse
import json
from fractions import Fraction


def intersection(start: int, end: int, clip_start: int, clip_end: int, fps: Fraction) -> dict:
    if fps <= 0 or end < start or clip_end < clip_start:
        raise ValueError('FPS must be positive and intervals must be ordered')
    left, right = max(start, clip_start), min(end, clip_end)
    if right <= left:
        return {'has_frames': False, 'frames': 0}
    return {'has_frames': True, 'start_frame': left, 'end_frame_exclusive': right,
            'frames': right-left, 'start_seconds': float(Fraction(left)/fps),
            'duration_seconds': float(Fraction(right-left)/fps), 'fps': str(fps)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['start', 'end', 'clip-start', 'clip-end']:
        parser.add_argument('--'+name, type=int, required=True)
    parser.add_argument('--fps', type=Fraction, required=True)
    args = parser.parse_args()
    try:
        result = intersection(args.start, args.end, args.clip_start, args.clip_end, args.fps)
    except ValueError as error:
        parser.exit(1, f'{error}\n')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

