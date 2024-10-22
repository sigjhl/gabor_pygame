# Gabor Patch Visual Search Training

This project is a visual search training application using Gabor patches. It challenges users to find matching patches within a time limit, recording scores for a leaderboard.

## Features

- Generate Gabor patches with different orientations, frequencies, and phases.
- Timed gameplay with score tracking.
- Leaderboard to display top scores.
- Intuitive GUI built with PyQt5.

## Installation

To run this application, ensure you have Python 3.6 or higher installed. You can set up a virtual environment and install the necessary packages.

### Step 1: Clone the repository

```bash
git clone https://github.com/sigjhl/gabor_pygame
cd gabor-patch-visual-search
```

### Step 2: Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### Step 3: Install dependencies

Install the required Python packages using pip:

```bash
pip install -r requirements.txt
```

## Usage

Run the application using the following command:

```bash
python gabor_patch_app.py
```

### Controls

- Click on the matching Gabor patches to score points.
- The game lasts for a set time limit, and scores will be recorded on the leaderboard.

## Leaderboard

At the end of each game, you have the option to save your score. The leaderboard will display your rank based on the highest patches/min scores.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or bugs.

## License

This project is licensed under the MIT License.
