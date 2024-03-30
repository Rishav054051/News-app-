import tkinter as tk
from tkinter import ttk,messagebox
import requests
import pyttsx3 
import multiprocessing
from PIL import Image,ImageTk
import io
import threading

Labelfont="elephanta 10 bold"
Entryfont="elephanta 10"
titlefont='Helvetica', 16, 'bold'

articles_loaded = 0
articles_per_load = 5  # Change this number according to your preference
load_more_button = None

def get_news(category):
    global news_canvas,news_frame,articles_loaded,articles_per_load,load_more_button
    # Clear previous news articles if it's the first load
    if articles_loaded == 0:
        for widget in news_frame.winfo_children():
            widget.destroy()

    #checking if the category is left empty. If yes, showing warning
    if not category:
        messagebox.showwarning("Empty Category","Please Enter a News Category")

    #if category is not empty and fetching news
    url = f"https://newsapi.org/v2/everything?language=en&q={category}&sortBy=publishedAt&apiKey=112d1223bb0e462f8a2a8aa33edb8909"

    response=requests.get(url)   #sending requests to server and getting the data
    news_data=response.json()    #parsing the data in python dictionary form
    articles=news_data.get('articles',[])   #formatting the data in key and value pair form

    if not articles:   #checking if the artciles is empty or not
        messagebox.showwarning("No News Found", "No news articles found for the entered category.")
        return
    
    # Load articles incrementally
    for i in range(articles_loaded, min(articles_loaded + articles_per_load, len(articles))):
        article = articles[i]
        title = article.get("title", "No Title")
        description = article.get("description", "No Description")
        author = article.get("author", "Unknown")
        source = article.get("source", {}).get("name", "Unknown")
        image_url = article.get("urlToImage")

        # Check if any essential information is missing or marked as removed
        if title == "[Removed]" or author == "[Removed]" or description == "[Removed]":
            continue

        # Display news information
        news_item = tk.Frame(news_frame)
        news_item.pack(anchor="w", padx=10, pady=10, fill="x")

        voice_buttons=tk.Frame(news_frame,bg="black")
        voice_buttons.pack(anchor="e",padx=10,pady=10,fill="x")

        tk.Label(news_item, text=title, font=titlefont).pack(anchor="w")  # Title
        if image_url:
            try:
                image_data = requests.get(image_url).content
                image = Image.open(io.BytesIO(image_data))
                image.thumbnail((100, 100))  # Resize image
                photo = ImageTk.PhotoImage(image)
                label = tk.Label(news_item, image=photo)
                label.image = photo  # Keep a reference to prevent garbage collection
                label.pack(side="left", padx=10)
            except Exception as e:
                print(f"Error loading image: {e}")
        tk.Label(news_item, text=f"Author: {author} | Source: {source}").pack(anchor='w')  #author
        tk.Label(news_item, text=f"Description: {description}").pack(anchor='w')   #description

        # Speak button
        speak_button = tk.Button(voice_buttons, text="Speak", command=lambda desc=description: speak_news(desc))
        speak_button.pack(padx=10)

        # Stop button
        stop_button = tk.Button(voice_buttons, text="Stop", command=lambda: stop_narration())
        stop_button.pack(padx=10)

        #updates the canvas while scrolling down with pending queues 
        news_canvas.update_idletasks()
        news_canvas.config(scrollregion=news_canvas.bbox("all"))
    
    articles_loaded += articles_per_load

    # Check if there are more articles to load
    if articles_loaded < len(articles):
        # Add "Load More" button if it's not already added
        if not load_more_button:
            load_more_button = tk.Button(news_frame, text="Load More", command=lambda: load_more_news(category))
            load_more_button.pack(side="bottom")
    else:
        # Remove the "Load More" button if all articles are loaded
        if load_more_button:
            load_more_button.pack_forget()
            load_more_button = None

    # Update the canvas while scrolling down with pending queues
    news_canvas.update_idletasks()
    news_canvas.config(scrollregion=news_canvas.bbox("all"))


def load_more_news(category):
    threading.Thread(target=get_news, args=(category,)).start()


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

def fetch_news():
    category = category_entry.get()
    threading.Thread(target=get_news, args=(category,)).start()

def run():
    global root,news_canvas,news_frame,category_entry
    root=tk.Tk()
    root.state("zoomed")  #make gui window fit for screen automatically
    root.resizable(0,0)   #setting the size of gui window constant
    root.title("News App")  #setting the title of GUI window
    root.protocol("WM_DELETE_WINDOW", on_closing)  # Bind the closing event to on_closing function

    #making the entry widget for entering the category of the news
    category_label=tk.Label(root,text="Enter News Category",font=Labelfont)
    category_label.pack()
    category_entry=tk.Entry(root,font=Entryfont)
    category_entry.pack()

    #making fetch button 
    fetch_button=tk.Button(root,text="Fetch News",command=fetch_news)
    fetch_button.pack()

    #creating canvas to hold the scrollbar
    news_canvas=tk.Canvas(root,bg="gray")
    news_canvas.pack(side=tk.LEFT,expand=True,fill="both")

    #creating a scrollbar
    scrollbar=ttk.Scrollbar(root,orient="vertical",command=news_canvas.yview)
    scrollbar.pack(side=tk.RIGHT,fill="y")

    #configuring the scrollbar for canvas
    news_canvas.config(yscrollcommand=scrollbar.set)

    #creating a frame inside the new_canvas for holding the news articles
    news_frame=tk.Frame(news_canvas)
    news_canvas.create_window((0,0),window=news_frame,anchor="nw")

    root.mainloop()

if __name__=="__main__":
    speak_process = None
    engine = None
    stop_flag = False    
    run()
        