interface VideoPlayerProps {
  src?: string;
  poster?: string;
  className?: string;
}

export const VideoPlayer = ({ src, poster, className }: VideoPlayerProps) => {
  return (
    <div className={className}>
      <video
        controls
        poster={poster}
        className="w-full rounded-2xl shadow-elevated"
        preload="metadata"
      >
        <source src={src || "https://sample-videos.com/video321/mp4/720/big_buck_bunny_720p_1mb.mp4"} type="video/mp4" />
        Your browser does not support the video tag.
      </video>
    </div>
  );
};
