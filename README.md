<p align="center">
  <img src="https://i.postimg.cc/5yp7DxHN/Chat-GPT-Image-13-2025-14-31-22.png" width="300" alt="pip-art logo">
</p>

<h1 align="center">pip-art</h1>

<p align="center">
  <strong>Tired of boring installation logs? Turn any long-running command into a visual delight!</strong>
</p>

<p align="center">
    <a href="#"><img src="https://img.shields.io/pypi/v/pip-art.svg" alt="PyPI"></a>
    <a href="#"><img src="https://img.shields.io/badge/python-3.7+-blue.svg" alt="Python version"></a>
    <a href="#"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
</p>

---

## 🤔 The Problem

We've all been there. You run a command like `pip install`, `npm install`, or `docker build`, and for the next few minutes, you're stuck watching this...

```
Collecting some-package.................. 12%
Downloading another-dependency........... 45%
Building wheels for collected packages...
...and so on... 😴
```

It's boring, it's messy, and it completely kills the joy of coding.

## ✨ The Solution

**`pip-art`** is a simple but powerful utility that completely transforms this experience. It hides all the visual clutter from your command and, instead, shows you beautiful, community-made pixel art and animations right in your terminal.

Now, while your command runs in the background, you get to watch this:

![Screenshot of pip-art in action](https://i.postimg.cc/PJZfMRN4/2025-07-13-142412.png)

When the process is finished, your terminal is clean, and you're greeted with a "Command finished!" message, crediting the artist.

## 🚀 Key Features

*   **Universal:** Works with **any** command-line tool, not just `pip`. Use it for `npm`, `git`, `docker`, or anything else.
*   **Hides the Clutter:** All standard output and errors from the wrapped command are hidden, giving you a clean, zen-like experience.
*   **GIF Support:** The gallery supports animated GIFs for an even more dynamic waiting experience!
*   **Community-Powered:** The entire art collection is sourced from a public GitHub repository, and anyone can contribute.
*   **Zero-Config:** Just install it and use it. It works out of the box.

## 🛠️ Installation

Installing `pip-art` is as simple as running:

```bash
pip install pip-art
```

## 💡 How to Use

Just prefix any command you want to run with `pip-art`. The tool will take over your terminal to display the art and will give you back control once the command is finished.

#### **Example: Installing Python packages**

```bash
pip-art pip install -r requirements.txt
```

#### **Example: Installing Node.js dependencies**

```bash
pip-art npm install
```

---

## 🖼️ Join the Gallery!

The soul of `pip-art` is its community-driven art gallery. Have a cool pixel art piece or a funny GIF? We'd love to feature it!

The process is simple and managed through our gallery repository: **[pip-art-gallery](https://github.com/YOUR_USERNAME/pip-art-gallery)**. *(You need to create this repository!)*

### How to Add Your Art

1.  **Prepare Your Files:**
    *   **Image File:** Your artwork can be a static `PNG` / `JPG` or an animated `GIF`.
    *   **Metadata File (Recommended):** Create a JSON file with the **exact same name** as your image file, but with a `.json` extension (e.g., `my-cool-art.json` for `my-cool-art.png`).

2.  **Metadata Format:**
    This file helps us credit you properly!
    ```json
    {
      "title": "Your Artwork Title",
      "author": "Your Name / Nickname",
      "description": "A short, fun description of your art."
    }
    ```

3.  **Submit to the Gallery:**
    *   Go to the `pip-art-gallery` repository's `images` folder.
    *   Click `Add file` > `Upload files` and drag & drop your image and `.json` file.
    *   Create a Pull Request.

That's it! Your submission will be reviewed and merged for everyone to enjoy.

## 🎯 Our Goal

The goal of `pip-art` is simple: to bring a little bit of joy and personality back into the development process. Even a small thing like waiting for an installation can be a moment of delight.

---

This project is licensed under the MIT License. 