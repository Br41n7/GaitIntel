import { useEffect, useRef } from "react";
import type { PoseFrame } from "../types/pose";
import { SKELETON_CONNECTIONS } from "../types/pose";

/**
 * Plays the source video with the pose skeleton drawn on top, synced by
 * timestamp. Landmarks are normalized 0-1 (MediaPipe convention), so the
 * canvas just needs to match the video's rendered size each frame.
 *
 * Frame lookup is linear-scan-nearest for v0.1 — fine at a few hundred
 * frames per clip. Switch to a binary search only if profiling shows it
 * matters once videos get longer.
 */
export default function PoseOverlayVideo({
  videoUrl,
  frames,
}: {
  videoUrl: string;
  frames: PoseFrame[];
}) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>();

  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || frames.length === 0) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const findNearestFrame = (t: number): PoseFrame => {
      let closest = frames[0];
      let closestDiff = Math.abs(frames[0].timestamp_s - t);
      for (const f of frames) {
        const diff = Math.abs(f.timestamp_s - t);
        if (diff < closestDiff) {
          closest = f;
          closestDiff = diff;
        }
      }
      return closest;
    };

    const draw = () => {
      if (video.videoWidth && video.videoHeight) {
        canvas.width = video.clientWidth;
        canvas.height = video.clientHeight;
      }
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const frame = findNearestFrame(video.currentTime);
      const toPixel = (x: number, y: number): [number, number] => [x * canvas.width, y * canvas.height];

      ctx.strokeStyle = "#22c55e";
      ctx.lineWidth = 2;
      for (const [a, b] of SKELETON_CONNECTIONS) {
        const la = frame.landmarks[a];
        const lb = frame.landmarks[b];
        if (!la || !lb) continue;
        if ((la.visibility ?? 1) < 0.3 || (lb.visibility ?? 1) < 0.3) continue;
        const [ax, ay] = toPixel(la.x, la.y);
        const [bx, by] = toPixel(lb.x, lb.y);
        ctx.beginPath();
        ctx.moveTo(ax, ay);
        ctx.lineTo(bx, by);
        ctx.stroke();
      }

      ctx.fillStyle = "#16a34a";
      for (const lm of Object.values(frame.landmarks)) {
        if ((lm.visibility ?? 1) < 0.3) continue;
        const [px, py] = toPixel(lm.x, lm.y);
        ctx.beginPath();
        ctx.arc(px, py, 3, 0, 2 * Math.PI);
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    rafRef.current = requestAnimationFrame(draw);
    return () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, [frames]);

  return (
    <div className="relative inline-block w-full max-w-xl">
      <video ref={videoRef} src={videoUrl} controls className="w-full rounded-lg bg-black" />
      <canvas ref={canvasRef} className="pointer-events-none absolute left-0 top-0 h-full w-full" />
    </div>
  );
}
