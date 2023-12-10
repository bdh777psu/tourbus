import os
from google.cloud import secretmanager
from flask import Flask, render_template, session, request, redirect 
from flask_session import Session   
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from setlipy import client
from flask_googlemaps import GoogleMaps


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

sfm = ''
sp = spotipy.Spotify()

tour_name = ''
city_name = ''
event_date = ''
venue_name = ''

@app.route('/')
def signin():
    """
    Route decorator for the root URL. Handles signing in.
    """

    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = SpotifyOAuth(client_id=access_secret_version('spotify_clientid'),
                                client_secret=access_secret_version('spotify_secret'),
                                redirect_uri='http://tourbus-c26hyhllla-uc.a.run.app:80',
                                cache_handler=cache_handler,
                                show_dialog=True,
                                scope='user-top-read')

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        
        global sp
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return redirect('/home')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()  
        return f'<center><h1><img src="/static/images/tourbus.png" alt="A tourbus" width="400"><br>\
                    <a href="{auth_url}">\
                        <img src="/static/images/loginbutton.png" alt="A tourbus" width="300">\
                    </a></h1></center>'
    else:
        # Step 3. Signed in, display data
        sp = spotipy.Spotify(auth_manager=auth_manager)
        return redirect('/home')


@app.route('/home', methods=["GET", "POST"])
def homepage():
    """
    Generate the homepage of the web application.
    This function handles the GET and POST requests to the root URL. If the request method is GET, it retrieves the top artists of the current user using the 'sp.current_user_top_artists()' method and assigns the retrieved artists to the 'artists' variable. If the request method is POST, it retrieves the search query from the form using the 'request.form.get("search")' method and searches for artists matching the query using the 'sp.search()' method. The retrieved artists are then assigned to the 'artists' variable.
    The retrieved artists are passed as a parameter to the 'render_template()' method along with the 'homepage.html' template, 'year' set to 0, and 'city' set to 'city'. The generated HTML is stored in the 'html' variable.
    Finally, the generated HTML is returned as the response to the client.

    Parameters:
    - None
    
    Returns:
    - html (str): The generated HTML for the homepage.
    """

    if request.method == "GET":
        top_artists = sp.current_user_top_artists()
        artists = top_artists['items']
    else:
        search = request.form.get("search")

        top_artists = sp.search(q=search, type='artist', limit=50)
        artists = top_artists['artists']['items']

    html = render_template('homepage.html',
                           artists=artists,
                           year = 0,
                           city = 'city')

    return html


@app.route('/artist/<id>/<year>/<city>', methods=["GET", "POST"])
def artist(id, year, city):
    """
    Define a route for retrieving artist information based on the artist's ID, the desired year, and the city.
    This route supports both GET and POST requests.

    Parameters:
    - id: str, the ID of the artist.
    - year: str, the desired year.
    - city: str, the desired city.

    Returns:
    - html: str, the rendered template containing artist information, related artists, an image URL, city information, event date, venue name, tracks, tour name, and markers.
    """

    artist = sp.artist(id)

    if artist['images']:
        image_url = artist['images'][0]['url']
    else:
        image_url = 'http://placecage.com/600/400'

    artistsdata = sp.artist_related_artists(id)
    related_artists = artistsdata['artists']

    artist_name = artist['name']

    setlists = get_sfm_setlists(artist_name, year, city)
    markers = get_map_markers(id, setlists)
    tracks = get_tracks(artist_name, setlists)
    
    html = render_template('artist.html',
                            artist=artist,
                            related_artists=related_artists,
                            image_url=image_url,
                            city=city_name,
                            event_date=event_date,
                            venue=venue_name,
                            tracks=tracks,
                            tour_name=tour_name,
                            markers=markers
                            )
    
    return html

def get_sfm_setlists(artist_name, year, city):
    """
    Retrieves a setlist of a specific artist for a given year and city.

    Args:
        artist_name (str): The name of the artist.
        year (str): The year of the setlist. If '0', all years will be considered.
        city (str): The city where the setlist was performed. If 'city', all cities will be considered.

    Returns:
        list: The setlist of the artist, in JSON format.

    Raises:
        KeyError: If no data is found for the specified city.
    """

    if request.method == "GET":
        city_name = None if city == 'city' else city
        year = None if year == '0' else year
    else:
        city_name = None
        year = request.form.get("year")

    sfmdata = sfm.setlists(artist_name=artist_name, year=year, city_name=city_name)

    try:
        json_dump = (sfmdata.json())
        return json_dump['setlist']
    except KeyError:
        print(f"No data found for {year}!")


def get_map_markers(id, setlists):
    """
    Generate a map markers list based on the given artist ID and setlists.

    Parameters:
        id (int): The ID of the artist.
        setlists (list): A list of setlists.

    Returns:
        list: A list of map markers.
    """

    markers = []
    
    try:
        for tour_stop in setlists:        
            lat = tour_stop['venue']['city']['coords']['lat']
            lng = tour_stop['venue']['city']['coords']['long']

            global city_name
            city_name = tour_stop['venue']['city']['name']

            global venue_name
            venue_name = tour_stop['venue']['name']

            global event_date
            event_date = tour_stop['eventDate'] 

            load_set = f"<a href='/artist/{id}/{event_date[-4:]}/{city_name}'>Listen to set</a>"
            info = city_name + " " + event_date + " " + venue_name + " " + load_set

            markers.append({'lat': lat, 'lng': lng, 'infobox': info})

        return markers
    except TypeError:
        print(f"No markers set for {city_name}!")

def get_tracks(artist_name, setlists):
    """
    Retrieves a dictionary of tracks for a given artist from a list of setlists.

    Args:
        artist_name (str): The name of the artist.
        setlists (list): A list of setlists.

    Returns:
        dict: A dictionary with the track names as keys and the preview URLs as values.

    Raises:
        KeyError: If the tour name or set(s) are not found for a specific city.

    """
    
    global tour_name
    global city_name
    global event_date
    global venue_name

    tour_stop = ''
    try:
        for setlist in setlists:
            if setlist['eventDate'] == event_date:
                tour_stop = setlist
                break
    except:
        print(f"Setlist not found for {city_name}!")
    
    tour_name = ''
    try:
        tour_name = tour_stop['tour']['name'] + " - "
    except KeyError:
        print(f"Tour name not found for {city_name}!")
    except TypeError:
        tour_name = ''
    
    tracks = {}
    try:
        for set in tour_stop['sets']['set']:
            for song in set['song']:
                song_name = song['name']
                songs = sp.search(q=f'{song_name}%20artist:{artist_name}', limit=1)
                
                tracks[song_name] = songs['tracks']['items'][0]
        return tracks
    except:
        tour_name = "Sorry, no tour for the selected year"
        city_name = ''
        event_date = ''
        venue_name = 'any venues'

        tracks['Fail'] = {'preview_url': '', 'external_urls': {'spotify':'https://open.spotify.com/track/5sluzb7VfBh5sBM8C8Nofa'}}
        return tracks

@app.route('/sign_out')
def sign_out():
    """
    Signs out the user by removing the "token_info" key from the session dictionary and redirects to the home page.

    Parameters:
    None

    Returns:
    None
    """
        
    session.pop("token_info", None)
    return redirect('/')


@app.errorhandler(404)
def pageNotFound(error):
    """
    A function that handles the 404 error. 

    Parameters:
    - error: the error that caused the 404 status code

    Returns:
    - The rendered HTML template for the error page
    """
    
    print(error)

    return render_template('error.html')


def access_secret_version(secret_id, version_id="latest"):
    """
    Accesses a secret version from the Secret Manager.

    :param secret_id: The ID of the secret.
    :type secret_id: str
    :param version_id: The ID of the version to access (default is "latest").
    :type version_id: str
    :return: The decoded payload of the secret version.
    :rtype: str
    """
        
    # Create the Secret Manager client.
    client = secretmanager.SecretManagerServiceClient()

    # Build the resource name of the secret version.
    name = f"projects/tourbus-407014/secrets/{secret_id}/versions/{version_id}"

    # Access the secret version.
    response = client.access_secret_version(name=name)

    # Return the decoded payload.
    return response.payload.data.decode('UTF-8')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))


maps = GoogleMaps(app, key=access_secret_version('google_maps'))
sfm = client.Setlipy(auth=access_secret_version('setlistfm'))