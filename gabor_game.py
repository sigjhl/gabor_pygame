import sys
import csv
import os
import random
import numpy as np
from PIL import Image
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton, 
                             QLabel, QGridLayout, QDialog, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QInputDialog)
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

def gabor_patch(size, lambda_, theta, sigma, phase, trim=.005):
    size = int(size)
    X0 = (np.linspace(1, size, size) / size) - .5
    freq = size / float(lambda_)
    phaseRad = (phase / 180.) * np.pi
    Xm, Ym = np.meshgrid(X0, X0)
    thetaRad = (theta / 180.) * np.pi
    Xt = Xm * np.cos(thetaRad)
    Yt = Ym * np.sin(thetaRad)
    grating = np.sin(((Xt + Yt) * freq * 2 * np.pi) + phaseRad)
    
    # Modified Gaussian envelope calculation to maintain size
    r = np.sqrt(Xm**2 + Ym**2)
    gauss = np.exp(-(r**2) / (2 * (sigma/100)**2))
    
    # Normalize the Gaussian to maintain contrast
    gauss = (gauss - gauss.min()) / (gauss.max() - gauss.min())
    
    # Apply the envelope
    img_data = (grating * gauss + 1) / 2 * 255
    
    # Ensure the image uses the full range
    img_data = ((img_data - img_data.min()) / (img_data.max() - img_data.min()) * 255)
    
    return Image.fromarray(img_data.astype(np.uint8))

class GaborPatch(QLabel):
    clicked = pyqtSignal()

    def __init__(self, orientation, lambda_, sigma, phase, size=100):
        super().__init__()
        self.orientation = orientation
        self.lambda_ = lambda_
        self.sigma = sigma
        self.phase = phase
        self.setAlignment(Qt.AlignCenter)
        self.setFixedSize(size, size)
        self.create_gabor_patch(size)

    def create_gabor_patch(self, size):
        patch = gabor_patch(size, self.lambda_, self.orientation, 
                           self.sigma, self.phase)
        qimage = QImage(patch.tobytes(), size, size, size, QImage.Format_Grayscale8)
        pixmap = QPixmap.fromImage(qimage)
        self.setPixmap(pixmap)

    def mousePressEvent(self, event):
        self.clicked.emit()

    def clone(self):
        return GaborPatch(self.orientation, self.lambda_, self.sigma, 
                         self.phase)

class LeaderboardDialog(QDialog):
    def __init__(self, scores):
        super().__init__()
        self.setWindowTitle('Leaderboard')
        self.setModal(True)
        self.resize(500, 400)
        
        layout = QVBoxLayout()
        
        # Create table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(['Rank', 'Patches/min', 'Total Score', 'Date/Time'])
        
        # Populate table with sorted scores (by patches_per_min)
        sorted_scores = sorted(scores, key=lambda x: float(x['patches_per_min']), reverse=True)
        self.table.setRowCount(len(sorted_scores))
        
        for i, score in enumerate(sorted_scores):
            self.table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.table.setItem(i, 1, QTableWidgetItem(f"{float(score['patches_per_min']):.2f}"))
            self.table.setItem(i, 2, QTableWidgetItem(score['score']))
            self.table.setItem(i, 3, QTableWidgetItem(score['date']))
            
        self.table.resizeColumnsToContents()
        layout.addWidget(self.table)
        
        close_button = QPushButton('Close')
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        
class GaborPatchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.scores_file = 'gabor_leaderboard.csv'
        self.initial_time = 180
        self.scores = []
        self.load_scores()
        self.initUI()
        
    def load_scores(self):
        if os.path.exists(self.scores_file):
            try:
                with open(self.scores_file, 'r', newline='') as f:
                    reader = csv.DictReader(f)
                    self.scores = list(reader)
            except Exception as e:
                print(f"Error loading scores: {e}")
                self.create_scores_file()
        else:
            self.create_scores_file()
            
    def create_scores_file(self):
        with open(self.scores_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['score', 'patches_per_min', 'date'])
            writer.writeheader()
        self.scores = []
            
    def save_scores(self):
        try:
            with open(self.scores_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['score', 'patches_per_min', 'date'])
                writer.writeheader()
                writer.writerows(self.scores)
                f.flush()  # Ensure writing to disk
                os.fsync(f.fileno())  # Force write to disk
        except Exception as e:
            print(f"Error saving scores: {e}")
            
    def add_score(self):
        # Calculate patches per minute
        time_played_minutes = (self.initial_time - self.game_time) / 60
        patches_per_min = self.score / time_played_minutes if time_played_minutes > 0 else 0
        
        score_entry = {
            'score': str(self.score),
            'patches_per_min': f"{patches_per_min:.2f}",
            'date': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        self.scores.append(score_entry)
        # Sort by patches per minute
        self.scores.sort(key=lambda x: float(x['patches_per_min']), reverse=True)
        self.scores = self.scores[:10]  # Keep only top 10
        self.save_scores()
        
    def show_leaderboard(self):
        dialog = LeaderboardDialog(self.scores)
        dialog.exec_()
        
    def initUI(self):
        self.setWindowTitle('Gabor Patch Visual Search Training')
        self.setGeometry(100, 100, 800, 900)
        
        layout = QVBoxLayout()
        
        # Top section with timer and score
        top_section = QVBoxLayout()
        self.time_label = QLabel('Time left: 3:00')
        self.instruction_label = QLabel('Find the matching Gabor patch to the highlighted one')
        self.score_label = QLabel('Score: 0')
        self.rate_label = QLabel('Current rate: 0.00 patches/min')  # New label for current rate
        top_section.addWidget(self.time_label)
        top_section.addWidget(self.instruction_label)
        top_section.addWidget(self.score_label)
        top_section.addWidget(self.rate_label)
        layout.addLayout(top_section)
        
        # Game grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        layout.addLayout(self.grid_layout)
        
        # Button section
        button_layout = QVBoxLayout()
        self.start_button = QPushButton('Start Game')
        self.start_button.clicked.connect(self.start_game)
        self.leaderboard_button = QPushButton('Show Leaderboard')
        self.leaderboard_button.clicked.connect(self.show_leaderboard)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.leaderboard_button)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        
        self.game_time = self.initial_time
        self.score = 0
        self.target_patch = None
        self.target_patches = []  # List to hold two target patches
        self.highlighted_patch = None  # Reference to the highlighted target patch
        
    def update_time(self):
        self.game_time -= 1
        minutes = self.game_time // 60
        seconds = self.game_time % 60
        self.time_label.setText(f'Time left: {minutes}:{seconds:02d}')
        
        # Update current rate
        time_played_minutes = (self.initial_time - self.game_time) / 60
        current_rate = self.score / time_played_minutes if time_played_minutes > 0 else 0
        self.rate_label.setText(f'Current rate: {current_rate:.2f} patches/min')
        
        if self.game_time <= 0:
            self.game_over()
            
    def game_over(self):
        self.timer.stop()
        self.start_button.setEnabled(True)
        
        time_played_minutes = (self.initial_time - self.game_time) / 60
        final_rate = self.score / time_played_minutes if time_played_minutes > 0 else 0
        
        # Create a message box to confirm saving the score
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Game Over")
        msg_box.setText(f"Final score: {self.score}\nRate: {final_rate:.2f} patches/min")
        msg_box.setInformativeText("Do you want to save your score to the leaderboard?")
        msg_box.setStandardButtons(QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
        msg_box.setDefaultButton(QMessageBox.Save)
        ret = msg_box.exec_()
        
        if ret == QMessageBox.Save:
            self.add_score()
            QMessageBox.information(self, "Score Saved", "Your score has been saved to the leaderboard.")
            self.show_leaderboard()
        elif ret == QMessageBox.Discard:
            QMessageBox.information(self, "Score Discarded", "Your score has been discarded.")
        # If Cancel, do nothing
            
    def start_game(self):
        time_limit, ok = QInputDialog.getInt(self, "Set Time Limit", 
                                           "Enter time limit in minutes:", 3, 1, 10)
        if ok:
            self.initial_time = time_limit * 60
            self.game_time = self.initial_time
            self.time_label.setText(f'Time left: {time_limit}:00')
            self.score = 0
            self.score_label.setText(f'Score: {self.score}')
            self.rate_label.setText('Current rate: 0.00 patches/min')
            self.timer.start(1000)
            self.generate_grid()
            self.start_button.setEnabled(False)
        
    def create_patch_set(self, n_total=36):
        # Parameters without inversion
        orientations = [0, 45, 90]
        lambdas = [15, 20, 30]
        phases = [0, 90, 180]
        sigma = 15
        
        used_combinations = set()
        patches = []
        
        # Step 1: Create 10 unique patterns
        while len(used_combinations) < 10:
            orientation = random.choice(orientations)
            lambda_ = random.choice(lambdas)
            phase = random.choice(phases)
            
            combination = (orientation, lambda_, phase)
            if combination in used_combinations:
                continue  # Skip duplicate combinations
            used_combinations.add(combination)
            
            patch = GaborPatch(orientation, lambda_, sigma, phase)
            patches.append(patch)
        
        # Step 2: Set one as target
        self.target_patch = random.choice(patches)
        patches.remove(self.target_patch)  # Remove target from patches
        
        # Step 3: Multiply the remaining 9 patterns by 4
        non_target_patches = patches.copy()
        multiplied_patches = []
        for patch in non_target_patches:
            for _ in range(4):
                multiplied_patches.append(patch.clone())
        
        # Ensure we have exactly 36 patches before inserting targets
        if len(multiplied_patches) != 36:
            QMessageBox.warning(self, "Patch Generation Warning",
                                f"Expected 36 non-target patches, but got {len(multiplied_patches)}.")
        
        # Step 4: Insert two target patches into the grid
        # Choose two unique random indices to replace with target patches
        replace_indices = random.sample(range(len(multiplied_patches)), 2)
        for idx in replace_indices:
            multiplied_patches[idx] = self.target_patch.clone()
        
        # Shuffle the final patches to randomize their positions
        random.shuffle(multiplied_patches)
        
        return multiplied_patches
    
    def generate_grid(self):
        # Clear existing patches from the grid
        for i in reversed(range(self.grid_layout.count())): 
            widget_to_remove = self.grid_layout.itemAt(i).widget()
            if widget_to_remove is not None:
                widget_to_remove.setParent(None)
        
        # Create 36 patches (6x6 grid)
        patches = self.create_patch_set(36)
        
        # Identify the two target patches in the grid
        self.target_patches = [patch for patch in patches if 
                               (patch.orientation == self.target_patch.orientation and
                                patch.lambda_ == self.target_patch.lambda_ and
                                patch.sigma == self.target_patch.sigma and
                                patch.phase == self.target_patch.phase)]
        
        if len(self.target_patches) != 2:
            QMessageBox.critical(self, "Patch Generation Error",
                                 f"Expected two target patches, but found {len(self.target_patches)}. Restarting grid generation.")
            self.generate_grid()  # Retry grid generation
            return
        
        # Randomly decide which target patch to highlight
        self.highlighted_patch = random.choice(self.target_patches)
        self.highlighted_patch.setStyleSheet("border: 4px solid green; padding: 2px; background-color: transparent;")
        
        # Add click handlers to all patches
        for patch in patches:
            patch.clicked.connect(self.check_match)
        
        # Layout patches in a 6x6 grid
        for i, patch in enumerate(patches):
            self.grid_layout.addWidget(patch, i // 6, i % 6)
    
    def check_match(self):
        sender = self.sender()
        if sender in self.target_patches and sender != self.highlighted_patch:
            # Correct selection, increase score and regenerate grid
            self.score += 1
            self.score_label.setText(f'Score: {self.score}')
            self.generate_grid()

    
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GaborPatchApp()
    ex.show()
    sys.exit(app.exec_())
