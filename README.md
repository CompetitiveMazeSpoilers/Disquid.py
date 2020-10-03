# Disquid.py
A Discord.py import of a Python game known as Conqid.

## Conquid Rules
Conquid is a simple strategy game based on a grid of colored (or uncolored) spaces. The uncolored spaces represent aqcuireable land, 
while the colored spaces represent player owned land, with each color representing a player.
Land may be aqcuired by any player at any time in groups of 3 on that player's turn as long as it is not taken by the other. 
Each player has a 2x2 base at either end of the game board, and the goal is to aquire/conquer land in a format that creates 
a line from one player's base to the other. The player that performs this task first is crowned the winner.

There are other moves as well, listed below:

Conquer: One player may overtake one cell of the other player's land as long as 2 of said player's own cells are touching that land. This counts as a turn.

Vanquish: A player may remove a 3x3 area of the other player's land as long as the enemy player owns every cell within a 3x3 area and the attempting player 
owns 3 connecting cells.

Conquest: The winning move. This must be used for the game to count as a win for the attempting player. Only succeeds if there is an unbroken line of cells
to the enemy player's base.

## Installation

Download the zip from the latest version, or use the Git implementation of your choice to open a branch and run in an IDE.

## Contribution

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please be sure to update tests as appropriate and required.

## Support

Contact William Greenlee on GitHub, or by email at greenlee04@gmail.com

## Authors

WGreenlee04 -- William Greenlee
Pqvqn
TortCode

## License
[MIT](https://choosealicense.com/licenses/mit/)
