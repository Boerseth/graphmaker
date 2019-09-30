# Graph-maker
This program takes an image of a curve, either svg or bitmap (jpg, png), and approximates it by Fourier series. The program outputs a picture of the graph and the equations of the approximation in LaTeX code. 

## Getting started

### Prerequisites
You will need to have Python and the packages PIL and Numpy installed in order to run the python script.

Paths saved in svg-format can be drawn with programs like InkScape.

The type of drawings that can be interpreted can be made in any visual tool that you prefer, from MS-Paint to PS.

### Installing
No install needed. It's just a script!

## Typical usage
The script is run with two parameters:
1. the file name of the image made into a graph
2. the number of Fourier-terms you want the progam to use in its approximation

So, as an example, you might run it as
```
$ python3 graph_maker.py image.png 100
```

## Requirements on the image files

### PNG - Drawing the curve in MS-Paint
You can draw your curve in MS-Paint and use the image file with this script. Here is how:

1. First, draw the curve in black on a white background. Make sure there is no antialiasing (gray colours mixed in to make the drawing look more smooth).
2. Make sure the curve does not intersect itself! It must alsopngbe closed and connected, that is you cannot lift the pencil and have to return to the starting point.
3. Once you are done drawing the curve, use the paint-bucket to fill in the outside of the curve with black colour.

After this you should have a black/white picture that is black on the outside of the curve and white on the inside, with no islands of either colour in the other region. There should also not be any grey-tones on the border between them. If you see that there are, try using other editing software to colour these pixels either white or black.

### SVG - Drawing a path in InkScape
This will perhaps lead to the most elegant graphs. Here is how you might go about doing this:

1. Find an image that you like and want to make a graph of
2. Open it in InkScape
3. Use the Bezier tool to trace out a curve on top of the image.
4. Make sure the curve you are making is connected! It also has to return to the starting point in the end.
5. When you are done drawing the curve and it is completed, it should change thickness and turn black.
6. You can now delete the picture you used as a guide. The curve should still be there.
7. Before saving the curve, make sure that InkScape is set up to save coordinates as absolute, not relative:
	1. Go to Edit->Preferences->SVG-output->Path data->Path string format
	2. Choose "Absolute"
8. Save the curve as an svg-file.

Now, simply run the program as described above, except using the right filename with svg-ending.
