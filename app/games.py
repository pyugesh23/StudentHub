from flask import Blueprint, render_template

games = Blueprint('games', __name__)

@games.route('/')
def hub():
    """Games Hub landing page."""
    games_list = [
        {
            'id': 'puzzle',
            'title': 'Puzzle Blocks',
            'description': 'Arrange scrambled blocks into the correct pattern. Challenges your spatial logic!',
            'icon': 'fa-puzzle-piece',
            'color': '#388bfd'
        },
        {
            'id': 'tictactoe',
            'title': 'Tic Tac Toe',
            'description': 'Classic strategy board game. Play against the system or a friend.',
            'icon': 'fa-times-circle',
            'color': '#f85149'
        },
        {
            'id': 'snake',
            'title': 'Snake Game',
            'description': 'Guide the snake to eat food and grow longer. Avoid hitting walls or yourself!',
            'icon': 'fa-staff-snake',
            'color': '#7ee787'
        },
        {
            'id': 'memory',
            'title': 'Memory Match',
            'description': 'Test your memory by matching pairs of cards in minimum moves.',
            'icon': 'fa-clone',
            'color': '#f1e05a'
        },
        {
            'id': 'rps',
            'title': 'Rock Paper Scissors',
            'description': 'Quick decision-based game against the system. Best of 5 mode!',
            'icon': 'fa-hand-back-fist',
            'color': '#ff7b72'
        },
        {
            'id': 'logic_puzzle',
            'title': 'Shape Sudoku',
            'description': 'Fill the grid with unique shapes in every row and column. A classic logic challenge!',
            'icon': 'fa-shapes',
            'color': '#ffca28'
        },
        {
            'id': 'equation_master',
            'title': 'Equation Master',
            'description': 'Solve unlimited math puzzles by filling in the blanks. Tests your mental math!',
            'icon': 'fa-calculator',
            'color': '#ff7b72'
        }
    ]
    return render_template('games/hub.html', games=games_list)

@games.route('/puzzle')
def puzzle():
    return render_template('games/puzzle.html')

@games.route('/tictactoe')
def tictactoe():
    return render_template('games/tictactoe.html')

@games.route('/snake')
def snake():
    return render_template('games/snake.html')

@games.route('/memory')
def memory():
    return render_template('games/memory.html')

@games.route('/rps')
def rps():
    return render_template('games/rps.html')

@games.route('/logic-puzzle')
def logic_puzzle():
    return render_template('games/logic_puzzle.html')

@games.route('/equation-master')
def equation_master():
    return render_template('games/equation_master.html')

