#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

#import json
import dateutil.parser
import babel
from flask import (
  Flask, 
  render_template, 
  request, 
  Response, 
  flash, 
  redirect, 
  url_for
)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import *
from sqlalchemy import func, desc


#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  venues = Venue.query.order_by(desc(Venue.id)).limit(10).all()
  artists = Artist.query.order_by(desc(Artist.id)).limit(10).all()
  return render_template('pages/home.html', venues=venues, artists=artists)


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  data = []
  all_locations = Venue.query.with_entities(Venue.city, Venue.state, func.count(Venue.id)).group_by(Venue.city, Venue.state).all()

  for location in all_locations:
    query_data = Venue.query.filter_by(state=location.state).filter_by(city=location.city).all()
    current_venues = []
    for loc in query_data:
      current_venues.append(
        {
          "id":loc.id,
          "name":loc.name
        }
      )
    data.append(
      {
        "city": location.city,
        "state": location.state,
        "venues": current_venues
      }
    )     
  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  q = request.form.get('search_term', '')
  venues = db.session.query(Venue).filter(Venue.name.ilike('%' + q + '%')).all()
  response={
        "count": len(venues),
        "data": venues
    }

  return render_template('pages/search_venues.html', results=response, search_term=q)
  

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id

  venue = Venue.query.get(venue_id)
  if not venue:
    return render_template('errors/404.html')

  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  
  upcoming_shows = []
  past_shows = []
  for show in upcoming_shows_query:
    temp = {  
      "venue_id": venue_id,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    }
    upcoming_shows.append(temp)

  for show in past_shows_query:
    temp = {  
      "venue_id": venue_id,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": str(show.start_time)
    }
    past_shows.append(temp)

  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website": venue.website,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows) ,
  }
  
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      name1 = request.form['name']
      city1= request.form['city']
      state1 = request.form['state']
      address1 = request.form['address']
      phone1 = request.form['phone']
      genres1 = request.form.getlist('genres')
      facebook_link1 = request.form['facebook_link']
      image_link1 = request.form['image_link']
      website1 = request.form['website_link']
      seeking_talent1 = True if 'seeking_talent' in request.form else False
      seeking_description1 = request.form['seeking_description']
      venue = Venue(name=name1, city=city1, state=state1, address=address1, phone=phone1, genres=genres1, 
        facebook_link=facebook_link1, image_link=image_link1,
        website=website1, seeking_talent=seeking_talent1, seeking_description=seeking_description1)
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + request.form['name'] + ' was successfully listed!') 
    except:
      db.session.rollback()  
      # TODO: on unsuccessful db insert, flash an error instead.
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    finally:    
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + err[0])
    flash('Errors ' + str(message))      

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  error = False
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
    error = True
  finally:
    db.session.close()
  
  if error:    
    flash('An error occurred. Please try again')    
  else:
    flash('Venue deleted.')
  
  return render_template('pages/home.html')
#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  q = request.form.get('search_term', '')
  artists = db.session.query(Artist).filter(Artist.name.ilike('%' + q + '%')).all()
  if not artists:
    return render_template('errors/404.html')

  response={
        "count": len(artists),
        "data": artists
    }
 
  return render_template('pages/search_artists.html', results=response, search_term=q)

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  query_artist = Artist.query.get(artist_id)
  upcoming_shows_query =db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  past_shows_query =db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()

  upcoming_shows = []
  past_shows = []
  for show in upcoming_shows_query:
    temp = {  
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.start_time)
    }
    upcoming_shows.append(temp)

  for show in past_shows_query:
    temp = {  
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": str(show.start_time)
    }
    past_shows.append(temp)    

  data={
    "id": artist_id,
    "name": query_artist.name,
    "genres": query_artist.genres,
    "city": query_artist.city,
    "state": query_artist.state,
    "phone": query_artist.phone,
    "website": query_artist.website,
    "facebook_link": query_artist.facebook_link,
    "seeking_venue": query_artist.seeking_venue,
    "seeking_description": query_artist.seeking_description,
    "image_link": query_artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
 
  artist = Artist.query.get(artist_id)
  
  if not artist:
    return render_template('errors/404.html')

  form = ArtistForm(
    name = artist.name,
    genres = artist.genres,
    city = artist.city,
    state = artist.state,
    phone = artist.phone,
    website = artist.website,
    facebook_link = artist.facebook_link,
    seeking_venue = artist.seeking_venue,
    seeking_description = artist.seeking_description,
    image_link = artist.image_link
  )
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      artist = Artist.query.get(artist_id)
      artist.name = request.form['name']
      artist.city= request.form['city']
      artist.state = request.form['state']
      artist.phone = request.form['phone']
      artist.genres = request.form.getlist('genres')
      artist.facebook_link = request.form['facebook_link']
      artist.image_link = request.form['image_link']
      artist.website = request.form['website_link']
      artist.seeking_venue = True if 'seeking_venue' in request.form else False
      artist.seeking_description = request.form['seeking_description']
      db.session.commit()
    except:
      db.session.rollback()  
      # on unsuccessful db update, flash an error instead.
      flash('An error occurred. Artist could not be updated.')
    finally:    
      db.session.close() 
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + err[0])
    flash('Errors ' + str(message))     
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get(venue_id)
  if not venue:
    return render_template('errors/404.html')

  form = VenueForm(
    name = venue.name,
    genres = venue.genres,
    address = venue.address,
    city = venue.city,
    state = venue.state,
    phone = venue.phone,
    website = venue.website,
    facebook_link = venue.facebook_link,
    seeking_talent = venue.seeking_talent,
    seeking_description = venue.seeking_description,
    image_link = venue.image_link
  )

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      venue = Venue.query.get(venue_id)
      venue.name = request.form['name']
      venue.city= request.form['city']
      venue.state = request.form['state']
      venue.address = request.form['address']
      venue.phone = request.form['phone']
      venue.genres = request.form.getlist('genres')
      venue.facebook_link = request.form['facebook_link']
      venue.image_link = request.form['image_link']
      venue.website = request.form['website_link']
      venue.seeking_talent = True if 'seeking_talent' in request.form else False
      venue.seeking_description = request.form['seeking_description']
      db.session.commit()
    except:
      db.session.rollback()  
      # TODO: on unsuccessful db update, flash an error instead.
      flash('An error occurred. Venue could not be updated.')
    finally:    
      db.session.close()  
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + err[0])
    flash('Errors ' + str(message))    

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # insert form data as a new Venue record in the db, instead
  # modify data to be the data object returned from db insertion
  form = ArtistForm(request.form, meta={'csrf': False})
  if form.validate():
    try:
      name1 = request.form['name']
      city1= request.form['city']
      state1 = request.form['state']
      phone1 = request.form['phone']
      genres1 = request.form.getlist('genres')
      facebook_link1 = request.form['facebook_link']
      image_link1 = request.form['image_link']
      website1 = request.form['website_link']
      seeking_venue1 = True if 'seeking_venue' in request.form else False
      seeking_description1 = request.form['seeking_description']
      artist = Artist(name=name1, city=city1, state=state1, phone=phone1, genres=genres1, 
        facebook_link=facebook_link1, image_link=image_link1,
        website=website1, seeking_venue=seeking_venue1, seeking_description=seeking_description1)
      db.session.add(artist)
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!') 
    except:
      db.session.rollback()  
      # on unsuccessful db insert, flash an error instead.
      # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
      flash('An error occurred. Artist could not be listed.')
    finally:    
      db.session.close()  
  else:
    message = []
    for field, err in form.errors.items():
        message.append(field + ' ' + err[0])
    flash('Errors ' + str(message))
  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  data=[]
  all_shows = Show.query.all()  
  if not all_shows:
    return render_template('errors/404.html')
  
  for each in all_shows:
    venue = Venue.query.get(each.venue_id)
    artist = Artist.query.get(each.artist_id)
    temp = {
    "venue_id": venue.id,
    "venue_name": venue.name,
    "artist_id": artist.id,
    "artist_name": artist.name,
    "artist_image_link": artist.image_link,
    "start_time": str(each.start_time)
    }
    data.append(temp)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # insert form data as a new Show record in the db, instead
  try:
    artist_id1 = request.form['artist_id']
    venue_id1= request.form['venue_id']
    start_time1 = request.form['start_time']  
    show = Show(artist_id =artist_id1, venue_id= venue_id1, start_time = start_time1)
    db.session.add(show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!') 
  except:
    db.session.rollback()  
    flash('An error occurred. Show could not be listed.')
  finally:    
    db.session.close()  

  # on successful db insert, flash success
  # on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
