import os
import re
import yt_dlp
import whisper
import moviepy.editor as mp
from moviepy.video.fx.all import crop
import google.generativeai as genai
import arabic_reshaper
from bidi.algorithm import get_display

def fix_arabic_text(text):
    """تهيئة النص العربي ليظهر متصلاً وصحيحاً على الفيديو"""
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def download_podcast(url):
    print("\n[1] جاري تحميل البودكاست بجودة مناسبة للريلز...")
    ydl_opts = {
        'format': 'bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]',
        'outtmpl': 'podcast.%(ext)s',
        'merge_output_format': 'mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    return "podcast.mp4"

def transcribe_audio(file_path):
    print("\n[2] جاري تفريغ الصوت وتحليل الكلمات...")
    model = whisper.load_model("base")
    result = model.transcribe(file_path)
    return result

def get_viral_clips(transcript_text, api_key):
    print("\n[3] جاري استخراج أفضل المقاطع باستخدام الذكاء الاصطناعي...")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    أنت خبير في صناعة المحتوى على تيك توك. اقرأ هذا النص المستخرج من بودكاست واستخرج منه أفضل اللحظات 
    التي تصلح كفيديوهات قصيرة (ريلز) جذابة. 
    استخرج أكبر عدد ممكن من المقاطع (حتى 100 مقطع إن وُجد).
    يجب أن تكون مدة المقطع بين 30 إلى 60 ثانية.
    
    أريد الإجابة فقط بتنسيق الأوقات بالثواني هكذا:
    Start-End
    مثال:
    15-60
    120-180
    
    النص:
    {transcript_text}
    """
    
    response = model.generate_content(prompt)
    clips = re.findall(r'(\d+)\s*-\s*(\d+)', response.text)
    return [(int(start), int(end)) for start, end in clips]

def create_reels_with_captions(video_path, clips, segments):
    print(f"\n[4] جاري قص {len(clips)} مقاطع وإضافة الكابشن...")
    video = mp.VideoFileClip(video_path)
    
    # تحويل أبعاد الفيديو إلى 9:16 (تيك توك)
    w, h = video.size
    target_w = int(h * 9/16)
    video = crop(video, width=target_w, height=h, x_center=w/2)
    
    for i, (start, end) in enumerate(clips):
        if end > video.duration:
            end = video.duration
            
        print(f"جاري إنتاج المقطع رقم {i+1}...")
        clip = video.subclip(start, end)
        
        # استخراج الكابشن الخاص بهذا المقطع
        text_clips = []
        for segment in segments:
            seg_start = segment['start']
            seg_end = segment['end']
            
            if seg_start >= start and seg_end <= end:
                text = fix_arabic_text(segment['text'])
                # إنشاء نص الكابشن
                txt_clip = mp.TextClip(text, fontsize=45, color='white', bg_color='black', font='Arial')
                txt_clip = txt_clip.set_position(('center', 'bottom')).set_duration(seg_end - seg_start)
                txt_clip = txt_clip.set_start(seg_start - start)
                text_clips.append(txt_clip)
        
        if text_clips:
            final_clip = mp.CompositeVideoClip([clip] + text_clips)
        else:
            final_clip = clip
            
        final_clip.write_videofile(f"reel_{i+1}.mp4", codec="libx264", audio_codec="aac", fps=24, preset="ultrafast")
    
    video.close()
    print("\n✅ تم الانتهاء بنجاح! تفقد مجلد الملفات لتحميل الريلز.")

if __name__ == "__main__":
    url = input("أدخل رابط البودكاست من يوتيوب: ")
    api_key = input("أدخل مفتاح API الخاص بـ Gemini: ")
    
    video_file = download_podcast(url)
    transcription = transcribe_audio(video_file)
    
    clips_timestamps = get_viral_clips(transcription['text'], api_key)
    
    if not clips_timestamps:
        print("لم يتمكن الذكاء الاصطناعي من استخراج مقاطع. يرجى التأكد من النص.")
    else:
        create_reels_with_captions(video_file, clips_timestamps, transcription['segments'])
