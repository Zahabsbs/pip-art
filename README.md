<p align="center">
  <img src="https://i.postimg.cc/5yp7DxHN/Chat-GPT-Image-13-2025-14-31-22.png" width="250" alt="pip-art logo">
</p>

<h1 align="center">pip-art</h1>

<p align="center">
  <strong>Why stare at boring logs? Turn any long-running command into a surprise art show in your terminal!</strong>
</p>

<p align="center">
    <a href="#"><img src="https://img.shields.io/pypi/v/pip-art.svg" alt="PyPI"></a>
    <a href="#"><img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python version"></a>
    <a href="#"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
</p>

---

## 🎨 The Philosophy

You run `pip install`, `npm install`, or `docker build` and watch lines of text scroll by. It's functional, but it's joyless. 

**`pip-art`** transforms this dead time into a moment of discovery and delight. It hides the messy logs and displays a random piece of art from a community-driven gallery, turning your terminal into a tiny art museum while you wait.

![Screenshot of pip-art in action](https://i.postimg.cc/4y0k7gb3/2025-07-15-124711.png)

When the command is done, you get your terminal back, plus a final success or failure report.

## 🚀 Features

*   **Universal:** Works with **any** command, not just `pip`.
*   **Clean Experience:** Hides command output for a calm, clutter-free wait.
*   **GIF & PNG & JPG Support:** The gallery welcomes static images and animations.
*   **Community-Powered:** All art comes from a public GitHub repository. Anyone can contribute!
*   **Fully Customizable:** Don't like the public gallery? **Create your own!** A simple config file lets you point `pip-art` to any gallery you want.

## 🛠️ Installation

```bash
pip install pip-art
```

## 💡 How to Use

Just prefix any command with `pip-art`:

```bash
# Instead of this...
pip install numpy pandas tensorflow

# ...do this!
pip-art pip install numpy pandas tensorflow
```

```bash
# Works with any command
pip-art npm install
pip-art docker build .
```

---

## 🖼️ Curate Your Own Experience: The Config File

This is where `pip-art` becomes *your* tool. You can tell it to use your very own art gallery instead of the public one. Want a gallery of only cat pictures? Or 8-bit landscapes? You can do it!

**How it works:**

1.  **Create a config file:** In your user's home directory, create a file named `.pip-art.toml`.
    *   On Windows: `C:\Users\YourUser\.pip-art.toml`
    *   On Linux/macOS: `~/.pip-art.toml`

2.  **Add your gallery:** Inside this file, add one line:

    ```toml
    # Point to your own GitHub repository's "images" folder
    gallery_repo = "YOUR_USERNAME/YOUR_GALLERY_REPO_NAME"
    ```

That's it! The next time you run `pip-art`, it will fetch art from *your* repository.

To go back to the default community gallery, simply delete or comment out this line.

## 🤝 How to Contribute

There are two great ways to contribute to the `pip-art` ecosystem:

### 1. Add Art to the Main Community Gallery

Have a great piece of art everyone should see? Add it to the main gallery!

The process is managed through our gallery repository: **[pip-art-gallery](https://github.com/YOUR_USERNAME/pip-art-gallery)**. *(This link should point to the actual default gallery repo you create).*

1.  **Prepare your files:**
    *   **Image File:** A `PNG`, `JPG`, or an animated `GIF`.
    *   **Metadata File (Optional but Recommended):** A `.json` file with the **exact same name** as your image (e.g., `my-art.json` for `my-art.png`).

2.  **Metadata Format:** This is how we credit you!
    ```json
    {
      "title": "Your Artwork Title",
      "author": "Your Name / Nickname",
      "description": "A short, fun description of your art."
    }
    ```

3.  **Submit a Pull Request:** Go to the gallery repo, upload your files to the `images` folder, and open a PR.

### 2. Create Your Own Gallery to Share

Made a cool themed gallery? Share it! Create a public GitHub repository, fill the `images` folder with art, and tell people to use your `gallery_repo` link in their config file.

---

This project is licensed under the MIT License.
Made with ❤️ to make the terminal a more joyful place. 