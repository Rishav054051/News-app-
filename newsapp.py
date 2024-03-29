import tkinter as tk
from tkinter import ttk, messagebox
import requests
from PIL import Image, ImageTk
import io
import multiprocessing
import pyttsx3

def get_news(category):
    global news_frame, news_canvas

    # Clear previous news articles
    for widget in news_frame.winfo_children():
        widget.destroy()

    if not category:
        messagebox.showwarning("Empty Category", "Please enter a news category.")
        return

    url = f"https://newsapi.org/v2/everything?q={category}&apiKey=112d1223bb0e462f8a2a8aa33edb8909"  # Replace 'YOUR_API_KEY' with your actual API key
    response = requests.get(url)
    news_data = response.json()
    articles = news_data.get('articles', [])

    if not articles:
        messagebox.showwarning("No News Found", "No news articles found for the entered category.")
        return

    for article in articles:
        title = article.get('title', 'No Title')
        description = article.get('description', 'No Description')
        author = article.get('author', 'Unknown')
        source = article.get('source', {}).get('name', 'Unknown')
        image_url = article.get('urlToImage')

        # Display news information
        news_item = tk.Frame(news_frame)
        news_item.pack(anchor='w', padx=10, pady=10, fill='x')

        tk.Label(news_item, text=title, font=('Helvetica', 16, 'bold')).pack(anchor='w')

        # Load and display image if URL is valid
        if image_url:
            try:
                image_data = requests.get(image_url).content
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((100, 100))  # Resize image
                photo = ImageTk.PhotoImage(image)
                label = tk.Label(news_item, image=photo)
                label.image = photo  # Keep a reference to prevent garbage collection
                label.pack(side='left', padx=10)
            except Exception as e:
                print(f"Error loading image: {e}")

        # Speak button
        speak_button = tk.Button(news_item, text="Speak", command=lambda desc=description: speak_news(desc))
        speak_button.pack(side='left', padx=10)

        # Stop button
        stop_button = tk.Button(news_item, text="Stop", command=lambda: stop_narration())
        stop_button.pack(side='left')

        tk.Label(news_item, text=f"Author: {author} | Source: {source}").pack(anchor='w')
        tk.Label(news_item, text=f"Description: {description}").pack(anchor='w')

    # Update the canvas scroll region to include the newly added widgets
    news_canvas.update_idletasks()
    news_canvas.config(scrollregion=news_canvas.bbox("all"))

def speak_news(description):
    global speak_process, stop_flag

    # Stop any ongoing narration
    stop_narration()

    # Start new narration
    speak_process = multiprocessing.Process(target=speak_process_worker, args=(description,))
    speak_process.start()
    stop_flag = False

def speak_process_worker(description):
    global engine, stop_flag
    engine = pyttsx3.init()
    engine.say(description)
    engine.runAndWait()

    # Check if the stop flag is set
    if stop_flag:
        engine.stop()

def stop_narration():
    global stop_flag
    stop_flag = True

    # Terminate ongoing narration process if exists
    if speak_process and speak_process.is_alive():
        speak_process.terminate()

def on_closing():
    stop_narration()
    root.destroy()

def run():
    global root, news_frame, news_canvas, category_entry

    root = tk.Tk()
    root.state('zoomed')
    root.title("News App")
    root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the closing event to on_closing function

    # Entry widget for user to input news category
    category_label = tk.Label(root, text="Enter news category:")
    category_label.pack()
    category_entry = tk.Entry(root)
    category_entry.pack()

    # Button to fetch news
    fetch_button = tk.Button(root, text="Fetch News", command=lambda: get_news(category_entry.get()))
    fetch_button.pack()

    # Create a canvas
    news_canvas = tk.Canvas(root)
    news_canvas.pack(side=tk.LEFT, fill='both', expand=True)

    # Add a scrollbar to the canvas
    scrollbar = ttk.Scrollbar(root, orient="vertical", command=news_canvas.yview)
    scrollbar.pack(side=tk.RIGHT, fill='y')

    # Configure the canvas to use the scrollbar
    news_canvas.config(yscrollcommand=scrollbar.set)

    # Create a frame inside the canvas to hold the news articles
    news_frame = tk.Frame(news_canvas)
    news_canvas.create_window((0, 0), window=news_frame, anchor="nw")

    root.mainloop()

if __name__ == "__main__":
    speak_process = None
    engine = None
    stop_flag = False
    run()
