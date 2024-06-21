import tkinter as tk
from tkinter import ttk, messagebox
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
import time
import pandas as pd
import re
import threading
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import numpy

# Web driver settings
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
driver = webdriver.Chrome(options=options)

# Function to perform web scraping
def perform_scraping(start_year, end_year, progress_var, progress_label):
    try:
        driver.get("https://www.globalcmt.org/CMTsearch.html")

        yr_input = driver.find_element(By.NAME, "yr")
        yr_input.clear()
        yr_input.send_keys(str(start_year))

        oyr_input = driver.find_element(By.NAME, "oyr")
        oyr_input.clear()
        oyr_input.send_keys(str(end_year))

        ymd_option = driver.find_element(By.XPATH, "//input[@type='radio' and @name='otype' and @value='ymd']")
        ymd_option.click()

        done_button = driver.find_element(By.XPATH, "//input[@type='submit' and @value='Done']")
        done_button.click()

        time.sleep(2)

        event_data_list = []

        while True:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            results_header = soup.find("h2", text="Results")

            if results_header:
                pre_elements = results_header.find_all_next("pre")

                for pre_element in pre_elements:
                    event_text = pre_element.get_text()
                    event_data_list.append(event_text)

            try:
                more_solutions_button = driver.find_element(By.LINK_TEXT, "More solutions")
                more_solutions_button.click()
                time.sleep(2)
            except NoSuchElementException:
                break

        # Saving data to a file (or further processing)
        with open("event_data.txt", "w") as file:
            for event_text in event_data_list:
                file.write(event_text)
                file.write("\n" + "-" * 50 + "\n")

        messagebox.showinfo("Success", "Data scraping completed successfully!")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {str(e)}")

    finally:
        driver.quit()
        progress_var.set(100)
        progress_label.config(text="Process complete.")

# Function to extract data using regex and save to CSV
def extract_and_save_to_csv(file_name):
    event_data_list = []
    current_event_data = {}
    datetime_pattern = re.compile(r"Date:\s+(\d{4})/\s*(\d{1,2})/\s*(\d{1,2})\s+Centroid\s+Time:\s+(\d{1,2}):\s*(\d{1,2}):\s*(\d{1,2}(?:\.\d+)?)\s+GMT")
    coordinates_pattern = re.compile(r"\bLat=\s*(-?\d+(\.\d+)?)\s+Lon=\s*(-?\d+(\.\d+)?)")
    magnitude_pattern = re.compile(r"\b(Mw)\s+=\s+(\d+\.\d+)\s+(mb)\s+=\s+(\d+\.\d+)\s+(Ms)\s+=\s+(\d+\.\d+)\s+(Scalar Moment)\s+=\s+(.+)")
   
    with open(file_name, "r") as file:
        for line in file:
            line = line.strip()
            date_match = datetime_pattern.search(line)
            coordinates_match = coordinates_pattern.search(line)
            magnitude_match = magnitude_pattern.search(line)
   
            if date_match:
                current_event_data["year"] = date_match.group(1)
                current_event_data["month"] = date_match.group(2)
                current_event_data["day"] = date_match.group(3)
                current_event_data["hour"] = date_match.group(4)
                current_event_data["minute"] = date_match.group(5)
                current_event_data["second"] = date_match.group(6)
            elif coordinates_match:
                current_event_data["Lat"] = coordinates_match.group(1)
                current_event_data["Lon"] = coordinates_match.group(3)
            elif magnitude_match:
                current_event_data["Mw"] = float(magnitude_match.group(2))  # Convertir a float
                current_event_data["mb"] = float(magnitude_match.group(4))  # Convertir a float
                current_event_data["Ms"] = float(magnitude_match.group(6))  # Convertir a float
                current_event_data["Scalar Moment"] = magnitude_match.group(8)
   
            elif line == "-" * 50:
                event_data_list.append(current_event_data)
                current_event_data = {}
   
    if current_event_data:
        event_data_list.append(current_event_data)
   
    df = pd.DataFrame(event_data_list)
    csv_file_name = "event_data.csv"
    df.to_csv(csv_file_name, index=False)
    return csv_file_name

# Function to start scraping process
def start_scraping():
    start_year = int(entry_start_year.get())
    end_year = int(entry_end_year.get())

    progress_var.set(0)
    progress_label.config(text="Scraping data...")

    scraping_thread = threading.Thread(target=perform_scraping, args=(start_year, end_year, progress_var, progress_label))
    scraping_thread.start()

# Function to perform linear regression
def perform_linear_regression():
    try:
        # Cargar datos desde el archivo CSV
        df = pd.read_csv("event_data.csv")

        # Seleccionar las columnas para la regresión lineal
        X = df['mb'].values.reshape(-1, 1)  # mb como variable independiente (X)
        y = df['Mw'].values  # Mw como variable dependiente (y)

        # Crear un modelo de regresión lineal
        model = LinearRegression()
        model.fit(X, y)

        # Obtener coeficientes
        intercept = model.intercept_
        slope = model.coef_[0]
        r2 = model.score(X, y)

        messagebox.showinfo("Linear Regression Results", f"Intercept: {intercept:.2f}\nSlope: {slope:.2f}\nR²: {r2:.2f}")

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred during linear regression: {str(e)}")

# GUI setup
root = tk.Tk()
root.title("Web Scraping & Linear Regression GUI")

frame = ttk.Frame(root, padding="20")
frame.grid()

label_start_year = ttk.Label(frame, text="Start Year:")
label_start_year.grid(row=0, column=0, padx=5, pady=5, sticky="w")

entry_start_year = ttk.Entry(frame, width=10)
entry_start_year.grid(row=0, column=1, padx=5, pady=5)

label_end_year = ttk.Label(frame, text="End Year:")
label_end_year.grid(row=1, column=0, padx=5, pady=5, sticky="w")

entry_end_year = ttk.Entry(frame, width=10)
entry_end_year.grid(row=1, column=1, padx=5, pady=5)

scrape_button = ttk.Button(frame, text="Scrape Data", command=start_scraping)
scrape_button.grid(row=2, column=0, columnspan=2, pady=10)

regression_button = ttk.Button(frame, text="Perform Linear Regression", command=perform_linear_regression)
regression_button.grid(row=3, column=0, columnspan=2, pady=10)

progress_label = ttk.Label(frame, text="")
progress_label.grid(row=4, column=0, columnspan=2, pady=5)

progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(frame, orient="horizontal", length=200, mode="determinate", variable=progress_var)
progress_bar.grid(row=5, column=0, columnspan=2, pady=5)

root.mainloop()
