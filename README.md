# Disquid.py
A Discord.py import of a Python game known as Conquid.

## Rules of Conquid
### Objective
Each player is given one HQ on the opposite side of the board from the opponent.
The goal is to build a path of your cell color from your HQ to your opponent's HQ and be the first to declare Conquest.
### Setup
#### Board Sizes
##### Small
The minimal 7 by 14 grid is meant for quick gameplay on the go, mostly on small sheets on paper.
It is not recommended for normal gameplay as the limited board quickly results in most usable space getting filled up.
##### Medium
A 14 by 28 grid with 2 by 2 HQ is optimal for normal gameplay.
The board is large enough to allow for complexity and large-scale strategy in deciding how to expand masses and build bridges.
Moreover, the board is small enough to prevent one from spending hours on a single game.
##### Large
The 21 by 42 grid with a 3 by 3 HQ is the gold standard in official Conquid gameplay.
It offers greater opportunity for complexity and large-scale strategy.
Be warned, games on this large of a scale are time consuming and best done over long breaks.
#### HeadQuarters
##### HQ Locations
Each player HQ should be centered vertically along the middle row of the board. 

Also, each HQ should be as close to the left and right walls as possible,
but leave enough space between each HQ and the wall to allow vanquish. So far, this space is 4 cells.
##### Coloring
Each player will have one base color and one cell color.

For a 3 by 3 HQ, the outer ring will be filled with the base color while the inner cell has the cell color.
For a 2 by 2 HQ, all of the base is colored with the base color.
### Gameplay
Starting with the player on the left, players will take turns executing moves on the board.
On a single turn, a player may do one of the following four options:
#### Acquire
Claim three empty cells as your own.
#### Conquer
For all opponent cells that are *adjacent* to two or more of your cells, take over them and make them your cells.
Notice that you may now be able to conquer additional cells from your opponent.
Apply the above step repeatedly until no more opponent cells can be conquered.
#### Vanquish
Delete any 4 by 4 block consisting of a single color(player, opponent, or even empty) and convert it to empty cells.
This is only possible if the said 4 by 4 block is *surrounded* by at least four of your cells.
#### Conquest
If there exists a *path* connecting a cell *adjacent* to your HQ with a cell *adjacent* to your opponent's HQ
that consists of only your cells, you may declare Conquest.
##### Definition of Terms
###### Adjacent
A cell is *adjacent* to another cell if they share an edge. Since cells that touch diagonally only share a corner, they are not adjacent to each other.
###### Surround
A cell is said to *surround* a 4 by 4 block if it is *adjacent* to a cell within the block, but is not itself within the block.
###### Path
A *path* of cells is a list of cells where each cell is *adjacent* to the cell that comes directly before and the cell that comes directly after it.
##### Unplayability of HeadQuarters
No cell contained within a HQ is considered valid for the purposes of conquering enemy cells, forming part of a vanquish block, or surrounding a vanquish block.
### Winning
The first player to perform a Conquest wins the game and ends the match.
Ceremonially, one of the winning paths of the winning player will be colored with that player's base color.

## Installation

Download the zip from the latest version, or use the Git implementation of your choice to open a branch and run in an IDE.

## Contribution

Please contact the developers to be granted access to contribute directly, feel free to pull and fork at any point.

## Support

Contact William Greenlee on GitHub, or by email at greenlee04@gmail.com

## Authors

WGreenlee04 -- William Greenlee

Pqvqn

TortCode

## License
[MIT](https://choosealicense.com/licenses/mit/)
