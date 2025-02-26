# Mario Super Sluggers Draft Tool

The **Mario Super Sluggers Draft Tool** is a web application designed to facilitate a smarter draft experience for an 8 person Mario Super Sluggers League. It allows users to draft players, track team rosters, and manage chemistry and hate relationships between players. The tool also provides recommendations for drafting outfielders and ensures that teams pick captains appropriately.

---

## Table of Contents

1. [Features](#features)
2. [Technologies Used](#technologies-used)
3. [Installation](#installation)
4. [How to Use](#how-to-use)
5. [File Structure](#file-structure)
6. [Contributing](#contributing)
7. [License](#license)
8. [Acknowledgments](#acknowledgments)

---

## Features

- **Draft Players**: Teams can draft players from a pool of available characters.
- **Team Rosters**: View each team's roster in real-time.
- **Chemistry and Hate Relationships**: Track which players have chemistry or hate relationships with each other.
- **Outfielder Recommendations**: Get recommendations for drafting outfielders based on speed and chemistry.
- **Captain Selection**: Ensure teams pick captains appropriately.
- **Final Rosters**: View all teams' rosters at the end of the draft.
- **Reset Draft**: Reset the draft to start over.

---

## Technologies Used

- **Frontend**:
  - HTML, CSS, JavaScript
  - Flask Templating (Jinja2)
- **Backend**:
  - Python (Flask framework)
- **Data Handling**:
  - Pandas (for data manipulation)
- **Styling**:
  - Custom CSS for a simple design
- **Version Control**:
  - Git and GitHub

---

## Installation

### Prerequisites

- Python 3.x
- Flask
- Pandas

### Steps

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/JohnKircher/SluggersDraft.git
   cd SluggersDraft
   ```

2. **Set Up a Virtual Environment** (Optional but Recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:

   ```bash
   python app.py
   ```

5. **Access the Application**: Open your browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000).

---

## How to Use

### Start the Draft:

- Open the application in your browser.
- Select a team to start drafting.
- ***If you want to change the team names: edit lines 15-22 in app.py***

### Draft Players:

- Use the top 5 recommendations or browse all available players.
- Draft players by clicking their names.

### View Rosters:

- Check each team's roster in real-time.
- View chemistry and hate relationships between players.

### Designate a Center Fielder (CF):

- Designate a CF from your roster to get outfielder recommendations.

### End of Draft:

- When all players are drafted, the application will display the final rosters.

### Reset the Draft:

- Use the "Reset Draft" button to start over.

---

## File Structure

```
 mario-super-sluggers-draft-tool/
├── app.py                              # Main Flask application
├── utils.py                            # Utility functions (e.g., chemistry calculations)
├── templates/                          # HTML templates
│   ├── index.html                      # Homepage with team selection
│   ├── draft.html                      # Draft interface
│   ├── roster.html                     # Team roster view
│   └── final_rosters.html              # Final rosters display
├── static/                             # Static files (CSS, JS)
│   ├── styles.css                      # Custom styles
│   └── script.js                       # JavaScript for interactivity
├── data/                               # Data files (Excel sheets)
│   ├── sortedmasterchem.xlsx           # Sorted chemsitry data
│   ├── Player Statistics.xlsx          # Player data from game files
│   └── Season Data.xlsx                # Player data from my personal Sluggers League
├── README.md                           # This file
└── requirements.txt                    # Python dependencies
```

---

## Contributing

Contributions are welcome! If you'd like to contribute to this project, please follow these steps:

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature/YourFeatureName
   ```
3. Commit your changes:
   ```bash
   git commit -m 'Add some feature'
   ```
4. Push to the branch:
   ```bash
   git push origin feature/YourFeatureName
   ```
5. Open a pull request.

---

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Inspired by the Mario Super Sluggers game.
- Built by John Kircher, Contributions by John Moroney

