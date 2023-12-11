
# Tourbus - Mapped gigographies powered by Spotify and Setlist.fm

Take a trip down memory lane and re-listen to your favorite concert setlists, with this Python/Flask app, powered by Spotify and Setlist.fm.


## References

Note: This app was written in Python 3.x 

The data comes [directly from Spotify](https://developer.spotify.com/web-api/endpoint-reference/) and only uses authenticated calls. It's paired  with the [Setlist.fm API](https://www.setlist.fm/) for songs played at each specific Tour stop.

The CSS styling comes [from Bootstrap 4](http://v4-alpha.getbootstrap.com/). The neat little HTML5 audio player comes [from the audio.js project](http://kolber.github.io/audiojs/).

The app as it stands is pretty basic; [if you can follow Flask's excellent documentation](http://flask.pocoo.org/docs/0.10/quickstart/), there shouldn't be too many surprises here.


## Requirements
Python 3.6 or newer.


## Clone and run the app

To try it out, you can clone this repo into some temp folder:

~~~sh
git clone https://github.com/bdh777psu/tourbus
cd tourbus
# run the app on localhost:5000
python app.py
~~~


## Local Installation via Docker
Before running inside a Docker container, a Docker image must be created. In the project directory run:

```bash
docker build -t tourbus .
```

```bash
docker run -d -p 8080:8080 tourbus
```

Then go to: http://localhost:8080


## Live demo

The app is also hosted on Google Cloud run: Visit and authenticate with Spotify at [https://tourbus-c26hyhllla-uc.a.run.app/](https://tourbus-c26hyhllla-uc.a.run.app/) in your browser to see your latest top artists:

Click on any of the results to go to an Artist-specific page, where you should find the latest stop on the latest Tour, with the corresponding playable setlist.


## Issues
If you found a bug or have a question, please open an issue. Email will not be replied.


## Author
Diogo Lessa


## License
Tourbus is available under the MIT license.
