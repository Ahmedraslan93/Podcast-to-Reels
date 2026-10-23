import os
import yt_dlp
import whisper
from moviepy.editor import VideoFileClip
import moviepy.video.fx.all as vfx

def download_youtube_video(url, output_name="podcast.mp4"):
    """1. تحميل الفيديو من يوتيوب"""
    print("جاري تحميل الفيديو...")
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4',
        'outtmpl': output_name,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return output_name

def transcribe_audio(video_path):
    """2. استخراج النص باستخدام Whisper"""
    print("جاري تفريغ الصوت إلى نص عربي...")
    model = whisper.load_model("base") # يمكنك استخدام 'small' أو 'medium' لدقة أعلى
    result = model.transcribe(video_path, language="ar")
    return result['text'], result['segments']

def find_best_clips(transcript):
    """
    3. تحليل النص لاختيار أفضل المقاطع
    هنا يتم ربط API الذكاء الاصطناعي (مثل Gemini) لإعطائه النص 
    والطلب منه إرجاع وقت البداية والنهاية لأفضل دقيقة.
    (كمثال تجريبي، سنفترض أنه اختار من الدقيقة 1 إلى 2)
    """
    print("جاري البحث عن اللحظات الفيروسية...")
    # يجب استبدال هذا الجزء بنداء لـ LLM API
    best_clips = [{"start": 60, "end": 120}] 
    return best_clips

def create_reel(video_path, start_time, end_time, output_name):
    """4. قص الفيديو وتحويله للوضع العمودي (9:16)"""
    print(f"جاري إنشاء الريل: {output_name}...")
    
    # تحميل المقطع وقصه
    clip = VideoFileClip(video_path).subclip(start_time, end_time)
    
    # حساب أبعاد المنتصف للقص العمودي
    (w, h) = clip.size
    target_ratio = 9 / 16
    new_width = int(h * target_ratio)
    x_center = w / 2
    
    # قص الشاشة من المنتصف (Center Crop)
    cropped_clip = clip.crop(
        x1=x_center - new_width/2, 
        y1=0, 
        x2=x_center + new_width/2, 
        y2=h
    )
    
    # يمكنك لاحقاً إضافة الكابشنز هنا باستخدام TextClip
    
    cropped_clip.write_videofile(output_name, codec="libx264", audio_codec="aac")
    print("تم الانتهاء بنجاح!")

# مسار التشغيل
if __name__ == "__main__":
    youtube_link = input("أدخل رابط البودكاست: ")
    
    video_file = download_youtube_video(youtube_link)
    transcript, segments = transcribe_audio(video_file)
    clips = find_best_clips(transcript)
    
    for i, clip in enumerate(clips):
        create_reel(video_file, clip["start"], clip["end"], f"reel_{i+1}.mp4")
