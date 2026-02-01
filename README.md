# Local File Organizer: AI File Management Run Entirely on Your Device, Privacy Assured

Tired of digital clutter? Overwhelmed by disorganized files scattered across your computer? Let AI do the heavy lifting! The Local File Organizer is your personal organizing assistant, using cutting-edge AI to bring order to your file chaos - all while respecting your privacy.

## How It Works 💡

Before:

```
/home/user/messy_documents/
├── IMG_20230515_140322.jpg
├── IMG_20230516_083045.jpg
├── IMG_20230517_192130.jpg
├── budget_2023.xlsx
├── meeting_notes_05152023.txt
├── project_proposal_draft.docx
├── random_thoughts.txt
├── recipe_chocolate_cake.pdf
├── scan0001.pdf
├── vacation_itinerary.docx
└── work_presentation.pptx

0 directories, 11 files
```

After:

```
/home/user/organized_documents/
├── Financial
│   └── 2023_Budget_Spreadsheet.xlsx
├── Food_and_Recipes
│   └── Chocolate_Cake_Recipe.pdf
├── Meetings_and_Notes
│   └── Team_Meeting_Notes_May_15_2023.txt
├── Personal
│   └── Random_Thoughts_and_Ideas.txt
├── Photos
│   ├── Cityscape_Sunset_May_17_2023.jpg
│   ├── Morning_Coffee_Shop_May_16_2023.jpg
│   └── Office_Team_Lunch_May_15_2023.jpg
├── Travel
│   └── Summer_Vacation_Itinerary_2023.docx
└── Work
    ├── Project_X_Proposal_Draft.docx
    ├── Quarterly_Sales_Report.pdf
    └── Marketing_Strategy_Presentation.pptx

7 directories, 11 files
```

## Updates 🚀

**[2026/02] v0.1.0**:
* 🤖 **Copilot Mode**: Interactive AI assistant for custom file organization - chat with AI to define your own sorting rules!
* 🎛️ **CLI Model Configuration**: Change AI models from command line with `--text-model` and `--image-model` flags
* 📚 **Extended Format Support**: 
  - Ebooks: `.epub`, `.mobi`, `.azw`, `.azw3`
  - Audio: `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.wma`
  - Video: `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`
* 🔍 **Duplicate File Detection**: Automatically find and manage duplicate files with customizable handling strategies
* 📊 **Organizational Methodologies**: Apply proven frameworks like Johnny Decimal, PARA, ACCESS, Zettelkasten, and LATCH
* 🐳 **Docker Support**: Easy deployment with Dockerfile and docker-compose

**[2024/09] v0.0.2**:
* Featured by [Nexa Gallery](https://nexaai.com/gallery) and [Nexa SDK Cookbook](https://github.com/NexaAI/nexa-sdk/tree/main/examples)!
* Dry Run Mode: check sorting results before committing changes
* Silent Mode: save all logs to a txt file for quieter operation
* Added file support:  `.md`, .`excel`, `.ppt`, and `.csv` 
* Three sorting options: by content, by date, and by type
* The default text model is now [Llama3.2 3B](https://nexaai.com/meta/Llama3.2-3B-Instruct/gguf-q3_K_M/file)
* Improved CLI interaction experience
* Added real-time progress bar for file analysis

Please update the project by deleting the original project folder and reinstalling the requirements. Refer to the installation guide from Step 4.


## Roadmap 📅

- [x] Copilot Mode: chat with AI to tell AI how you want to sort the file (ie. read and rename all the PDFs)
- [x] Change models with CLI 
- [x] ebook format support
- [x] audio file support
- [x] video file support
- [x] Implement best practices like Johnny Decimal, PARA, ACCESS, Zettelkasten, LATCH
- [x] Check file duplication
- [x] Dockerfile for easier installation
- [ ] People from [Nexa](https://github.com/NexaAI/nexa-sdk) is helping me to make executables for macOS, Linux and Windows

## New Features 🎉

### Copilot Mode
Interactive AI assistant that allows you to chat with AI to define custom file organization rules. Simply describe how you want your files organized, and the AI will help you create and apply custom sorting rules.

**Usage:**
```bash
python main.py
# Select option 4: Copilot Mode
```

### CLI Model Configuration
Configure AI models directly from the command line. Choose different text and image models based on your needs.

**Usage:**
```bash
# List available models
python main.py --list-models

# Use custom models
python main.py --text-model "Llama3.2-1B-Instruct:q4_0" --image-model "llava-phi-3-mini:q4_0"
```

### Extended Format Support
Now supports additional file formats:
- **Ebooks:** `.epub`, `.mobi`, `.azw`, `.azw3`
- **Audio:** `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.wma`
- **Video:** `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`, `.mpeg`, `.mpg`

### Duplicate File Detection
Automatically detect and manage duplicate files during organization with three handling strategies:
1. Keep first occurrence only
2. Keep all duplicates with unique names
3. Skip all duplicates

### Organizational Methodologies
Apply proven organizational frameworks to your file structure:
- **Johnny Decimal:** Hierarchical organization with numeric categories (10.01, 20.05, etc.)
- **PARA:** Projects, Areas, Resources, Archives - productivity-focused organization
- **ACCESS:** Activities, Clients, Courses, Events, Systems, Sources
- **Zettelkasten:** Knowledge management with timestamped atomic notes
- **LATCH:** Location, Alphabet, Time, Category, Hierarchy

### Docker Support
Easy deployment and installation using Docker.

**Usage:**
```bash
# Build and run with docker-compose
docker-compose up

# Or build manually
docker build -t file-organizer .
docker run -it -v ./input:/data/input -v ./output:/data/output file-organizer
```

## What It Does 🔍

This intelligent file organizer harnesses the power of advanced AI models, including language models (LMs) and vision-language models (VLMs), to automate the process of organizing files by:


* Scanning a specified input directory for files.
* Content Understanding: 
  - **Textual Analysis**: Uses the [Llama3.2 3B](https://nexaai.com/meta/Llama3.2-3B-Instruct/gguf-q3_K_M/file) to analyze and summarize text-based content, generating relevant descriptions and filenames.
  - **Visual Content Analysis**: Uses the [LLaVA-v1.6](https://nexaai.com/liuhaotian/llava-v1.6-vicuna-7b/gguf-q4_0/file) , based on Vicuna-7B, to interpret visual files such as images, providing context-aware categorization and descriptions.

* Understanding the content of your files (text, images, and more) to generate relevant descriptions, folder names, and filenames.
* Organizing the files into a new directory structure based on the generated metadata.

The best part? All AI processing happens 100% on your local device using the [Nexa SDK](https://github.com/NexaAI/nexa-sdk). No internet connection required, no data leaves your computer, and no AI API is needed - keeping your files completely private and secure.


## Supported File Types 📁

- **Images:** `.png`, `.jpg`, `.jpeg`, `.gif`, `.bmp`
- **Text Files:** `.txt`, `.docx`, `.md`
- **Spreadsheets:** `.xlsx`, `.csv`
- **Presentations:** `.ppt`, `.pptx`
- **PDFs:** `.pdf`
- **Ebooks:** `.epub`, `.mobi`, `.azw`, `.azw3` (requires `ebooklib` and `beautifulsoup4`)
- **Audio:** `.mp3`, `.wav`, `.flac`, `.m4a`, `.aac`, `.ogg`, `.wma`
- **Video:** `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`, `.webm`, `.mpeg`, `.mpg`

**Note:** Audio and video files can be organized by type or date, but content-based organization (reading/analyzing content) is not available for multimedia files.

## Prerequisites 💻

- **Operating System:** Compatible with Windows, macOS, and Linux.
- **Python Version:** Python 3.12
- **Conda:** Anaconda or Miniconda installed.
- **Git:** For cloning the repository (or you can download the code as a ZIP file).

## Installation 🛠

> For SDK installation and model-related issues, please post on [here](https://github.com/NexaAI/nexa-sdk/issues).

### 1. Install Python

Before installing the Local File Organizer, make sure you have Python installed on your system. We recommend using Python 3.12 or later.

You can download Python from [the official website]((https://www.python.org/downloads/)).

Follow the installation instructions for your operating system.

### 2. Clone the Repository

Clone this repository to your local machine using Git:

```zsh
git clone https://github.com/QiuYannnn/Local-File-Organizer.git
```

Or download the repository as a ZIP file and extract it to your desired location.

### 3. Set Up the Python Environment

Create a new Conda environment named `local_file_organizer` with Python 3.12:

```zsh
conda create --name local_file_organizer python=3.12
```

Activate the environment:

```zsh
conda activate local_file_organizer
```

### 4. Install Nexa SDK ️

#### CPU Installation
To install the CPU version of Nexa SDK, run:
```bash
pip install nexaai --prefer-binary --index-url https://nexaai.github.io/nexa-sdk/whl/cpu --extra-index-url https://pypi.org/simple --no-cache-dir
```

#### GPU Installation (Metal - macOS)
For the GPU version supporting Metal (macOS), run:
```bash
CMAKE_ARGS="-DGGML_METAL=ON -DSD_METAL=ON" pip install nexaai --prefer-binary --index-url https://nexaai.github.io/nexa-sdk/whl/metal --extra-index-url https://pypi.org/simple --no-cache-dir
```
For detailed installation instructions of Nexa SDK for **CUDA** and **AMD GPU** support, please refer to the [Installation section](https://github.com/NexaAI/nexa-sdk?tab=readme-ov-file#installation) in the main README.


### 5. Install Dependencies 

1. Ensure you are in the project directory:
   ```zsh
   cd path/to/Local-File-Organizer
   ```
   Replace `path/to/Local-File-Organizer` with the actual path where you cloned or extracted the project.

2. Install the required dependencies:
   ```zsh
   pip install -r requirements.txt
   ```

**Note:** If you encounter issues with any packages, install them individually:

```zsh
pip install nexa Pillow pytesseract PyMuPDF python-docx ebooklib beautifulsoup4
```

With the environment activated and dependencies installed, run the script using:

### 6. Running the Script🎉
```zsh
python main.py
```

## Docker Installation (Alternative) 🐳

If you prefer using Docker for easier setup and isolation:

### 1. Install Docker

Download and install Docker Desktop from [docker.com](https://www.docker.com/products/docker-desktop).

### 2. Clone the Repository

```bash
git clone https://github.com/QiuYannnn/Local-File-Organizer.git
cd Local-File-Organizer
```

### 3. Prepare Your Files

Create `input` and `output` directories:

```bash
mkdir input output
```

Place the files you want to organize in the `input` directory.

### 4. Run with Docker Compose

```bash
docker-compose up
```

This will:
- Build the Docker image with all dependencies
- Mount your input/output directories
- Start the interactive file organizer
- Cache AI models for faster subsequent runs

### 5. Alternative: Manual Docker Build

```bash
# Build the image
docker build -t file-organizer .

# Run interactively
docker run -it \
  -v $(pwd)/input:/data/input \
  -v $(pwd)/output:/data/output \
  -v ~/.cache/nexa:/root/.cache/nexa \
  file-organizer
```

**Docker Notes:**
- Models are cached in `~/.cache/nexa` to avoid re-downloading
- The container runs interactively, allowing you to respond to prompts
- Your files remain on your local machine; Docker only provides the runtime environment

## Notes

- **SDK Models:**
  - The script uses `NexaVLMInference` and `NexaTextInference` models [usage](https://docs.nexaai.com/sdk/python-interface/gguf).
  - Ensure you have access to these models and they are correctly set up.
  - You may need to download model files or configure paths.


- **Dependencies:**
  - **pytesseract:** Requires Tesseract OCR installed on your system.
    - **macOS:** `brew install tesseract`
    - **Ubuntu/Linux:** `sudo apt-get install tesseract-ocr`
    - **Windows:** Download from [Tesseract OCR Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki)
  - **PyMuPDF (fitz):** Used for reading PDFs.

- **Processing Time:**
  - Processing may take time depending on the number and size of files.
  - The script uses multiprocessing to improve performance.

- **Customizing Prompts:**
  - You can adjust prompts in `data_processing.py` to change how metadata is generated.

## License

This project is dual-licensed under the MIT License and Apache 2.0 License. You may choose which license you prefer to use for this project.

- See the [MIT License](LICENSE-MIT) for more details.