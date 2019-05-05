# City-Cutter
A telegram bot that cuts given city with Voronoi diagram according to points that correspond to given place name (store, cinema...)

## Use
To use this telegram bot, you should type in PM: "/cut_the_city '{name of city}' '{name of place}'".
If everything goes well, you'll recieve an image.

Everything should look like this:
![alt text][example]

[example]: https://raw.githubusercontent.com/Shushpancheak/City-Cutter/dev/images/example.png "An example"

## Execution
You will need config.ini with API keys in it.
I can give my config.ini, or you can create your own:

first line is tg bot API key,
and the second line is gmaps API key with all possible APIs enabled.

```bash
pip install -r requirements.txt
python app.py
```

You will propably need to change imports in VoronoiDiagram package... And add __init__.py
