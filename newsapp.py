import tkinter as tk
from tkinter import ttk, messagebox
import requests
import pyttsx3 
import multiprocessing
from PIL import Image, ImageTk
import io
import threading

# Font styles
Labelfont = "Helvetica 12 bold"
Entryfont = "Helvetica 12"
Titlefont = "Helvetica 14 bold"

# Global variables
articles_loaded = 0
articles_per_load = 5
load_more_button = None
stop_flag = False

def get_news(category):
    global news_canvas, news_frame, articles_loaded, articles_per_load, load_more_button
    
    # Clear previous news articles if it's the first load
    if articles_loaded == 0:
        for widget in news_frame.winfo_children():
            widget.destroy()

    # Check if the category is empty
    if not category:
        messagebox.showwarning("Empty Category", "Please enter a news category")
        return

    # Fetch news based on the category
    url = f"https://newsapi.org/v2/everything?language=en&q={category}&sortBy=publishedAt&apiKey=112d1223bb0e462f8a2a8aa33edb8909"
    response = requests.get(url)
    news_data = response.json()
    articles = news_data.get('articles', [])

    if not articles:
        messagebox.showwarning("No News Found", "No news articles found for the entered category")
        return

    # Load articles incrementally
    for i in range(articles_loaded, min(articles_loaded + articles_per_load, len(articles))):
        article = articles[i]
        title = article.get("title", "No Title")
        description = article.get("description", "No Description")
        author = article.get("author", "Unknown")
        source = article.get("source", {}).get("name", "Unknown")
        image_url = article.get("urlToImage")

        # Check if essential information is missing
        if title == "[Removed]" or author == "[Removed]" or description == "[Removed]":
            continue

        # Display news information
        news_item = tk.Frame(news_frame, bd=1, relief="solid")
        news_item.pack(anchor="w", padx=10, pady=10, fill="x")

        # Title
        title_label = tk.Label(news_item, text=title, font=Titlefont, wraplength=600)
        title_label.pack(anchor="w", padx=(10, 0), pady=(10, 5))

        # Author and Source
        author_label = tk.Label(news_item, text=f"Author: {author} | Source: {source}", font=Labelfont)
        author_label.pack(anchor='w', padx=(10, 0))

        # Image
        if image_url:
            try:
                image_data = requests.get(image_url).content
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(image)
                label = tk.Label(news_item, image=photo)
                label.image = photo
                label.pack(side="left", padx=(10, 0))
            except Exception as e:
                print(f"Error loading image: {e}")

        # Description
        desc_text = tk.Text(news_item, wrap="word", height=4, width=80, font=Entryfont)
        desc_text.insert("1.0", description)
        desc_text.configure(state="disabled")
        desc_text.pack(anchor="w", padx=(10, 0), pady=(0, 5))

        # Voice Buttons
        voice_buttons = tk.Frame(news_item)
        voice_buttons.pack(anchor="e", padx=(0, 10), pady=(0, 10))

        # Load the icon image
        # Load the icon image
        icon_image = Image.open("speaker.png")
        icon_image = icon_image.resize((40, 40), Image.LANCZOS)  # Resize the image if needed
        icon_photo = ImageTk.PhotoImage(icon_image)

        #speak button
        speak_button = tk.Button(voice_buttons,image=icon_photo, text="Speak", command=lambda desc=description, tit=title: speak_news(desc,tit))
        speak_button.image = icon_photo
        speak_button.pack(side="left", padx=5)

        #stop button
        stop_button = tk.Button(voice_buttons, text="Stop",font='elephanta 15 bold', command=lambda: stop_narration())
        stop_button.pack(side="left", padx=5)

        # Update the canvas
        news_canvas.update_idletasks()
        news_canvas.config(scrollregion=news_canvas.bbox("all"))

    articles_loaded += articles_per_load

    # Check if there are more articles to load
    if articles_loaded < len(articles):
        if not load_more_button:
            load_more_button = tk.Button(news_frame, text="Load More", command=lambda: load_more_news(category))
            load_more_button.pack(side="bottom", pady=10)
    else:
        if load_more_button:
            load_more_button.pack_forget()
            load_more_button = None

    # Update the canvas
    news_canvas.update_idletasks()
    news_canvas.config(scrollregion=news_canvas.bbox("all"))

def load_more_news(category):
    threading.Thread(target=get_news, args=(category,)).start()

def speak_news(description,tit):
    global speak_process, stop_flag
    stop_narration()
    speak_process = multiprocessing.Process(target=speak_process_worker, args=(description,tit,))
    speak_process.start()
    stop_flag = False

def speak_process_worker(description,tit):
    global engine, stop_flag
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    engine.say(tit)
    engine.say(description)
    engine.runAndWait()
    if stop_flag:
        engine.stop()

def stop_narration():
    global stop_flag
    stop_flag = True
    if speak_process and speak_process.is_alive():
        speak_process.terminate()

def on_closing():
    stop_narration()
    root.destroy()

def fetch_news():
    category = category_entry.get()
    threading.Thread(target=get_news, args=(category,)).start()

def run():
    global root, news_canvas, news_frame, category_entry
    root = tk.Tk()
    root.state("zoomed")
    root.title("News App")
    root.protocol("WM_DELETE_WINDOW", on_closing)

    category_label = tk.Label(root, text="Enter News Category", font=Labelfont)
    category_label.pack(pady=(20, 0))

    category_entry = tk.Entry(root, font=Entryfont)
    category_entry.pack(pady=(5, 0))

    fetch_button = tk.Button(root, text="Fetch News", command=fetch_news)
    fetch_button.pack(pady=(10, 20))

    root.bind('<Return>', lambda event=None: fetch_news())

    news_canvas = tk.Canvas(root)
    news_canvas.pack(side=tk.LEFT, expand=True, fill="both")

    scrollbar = ttk.Scrollbar(root, orient="vertical", command=news_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill="y")

    news_canvas.config(yscrollcommand=scrollbar.set)

    h_scrollbar = ttk.Scrollbar(root, orient="horizontal", command=news_canvas.xview)
    h_scrollbar.pack(side=tk.BOTTOM, fill="x")

    news_canvas.config(xscrollcommand=h_scrollbar.set)

    news_frame = tk.Frame(news_canvas)
    news_frame.pack(fill="both", expand=True)
    news_canvas.create_window((0, 0), window=news_frame, anchor="nw")

    news_canvas.bind_all("<MouseWheel>", lambda event: news_canvas.yview_scroll(-1 * int(event.delta / 120), "units"))
    news_canvas.bind_all("<Shift-MouseWheel>", lambda event: news_canvas.xview_scroll(-1 * int(event.delta / 120), "units"))

    root.mainloop()

if __name__ == "__main__":
    speak_process = None
    engine = None  
    run()
