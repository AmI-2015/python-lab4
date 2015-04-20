#!/usr/bin/python

'''
Created on Apr 13, 2015

@author: bonino
'''
import signal
import getopt
import sys
from flask import Flask, jsonify, abort, request, render_template
from musiclib import TrackList, Player, AlbumList

app = None
track_list = None
album_list = None 
player = None 

# handle sigterm
def cleanup_on_term():
    player.exit()

# attach cleanup
signal.signal(signal.SIGTERM, cleanup_on_term)

# initialize the app
app = Flask(__name__)

# --------- SIMPLE WEB APP ----------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/playlist')
def playlist():
    return render_template('playlist.html', playlist=player.current_playlist)

@app.route('/album')
def album():
    return render_template('album.html', albumlist=album_list.albums)
@app.route('/album/<int:album_id>')
def album_single(album_id):
    return render_template('album_single.html', album = album_list.get_album(album_id))

# ---------  REST SERVER ------------------------------

@app.route('/music/api/v1.0/tracks', methods=['GET'])
def get_tracks():    
    #the response body to return
    response_body = None
    
    if(len(request.args) == 0):
        # return the track data
        response_body = jsonify({'tracks': [track.jsonifiable() for track in track_list.tracks]})
    else:
        #return the filtered track
        response_body = jsonify({'tracks': [track.jsonifiable() for track in track_list.search(request.args)]})

    #return the righ response body
    return response_body

@app.route('/music/api/v1.0/tracks/<int:track_id>', methods=['GET'])
def get_track(track_id):
    
    #this section might generate runtime errors
    try:
        # get the track
        track = track_list.get_track(int(track_id))
        
        # if no track has the given id return 404 not found
        if track == None:
            abort(404)
        
        # convert the track in its json representation
        return jsonify({'track': track.jsonifiable()})
    
    except:
        abort(500)

@app.route('/music/api/v1.0/albums',methods=['GET'])
def get_albums():
    
    #return the album list
    return jsonify({'albums':[album.jsonifiable() for album in album_list.albums]})

@app.route('/music/api/v1.0/albums/<int:album_id>', methods=['GET'])
def get_album(album_id):
    
    #this section might generate runtime errors
    try:
        # get the album
        album = album_list.get_album(album_id)
        
        # if no track has the given id return 404 not found
        if album == None:
            abort(404)
        
        # convert the album in its json representation
        return jsonify({'album': album.jsonifiable()})
    except:
        abort(500)


@app.route('/music/api/v1.0/player', methods=['PUT'])
def control_player():
    
    # get the request body
    play_request = request.json
    
    #check if a command is present
    if('command' in play_request):        
        
        # get the command
        command = play_request['command']
        
        #this portion of code might generate exceptions    
        try:
                        
            # PLAY
            if command.lower() == 'play':          
                # check direct track if any
                if "track" in play_request:
                    
                    # get the track id
                    track_id = play_request["track"]
                    
                    # check not empty nor None
                    if(track_id != None) and (track_id!=""):
                        
                        # get the track
                        track = track_list.get_track(int(track_id))
                       
                        #check that the track exists
                        if(track != None):
                            # debug
                            print ("playing file: \"%s\"\n" % track.path)
                       
                            # play the track
                            player.load_and_play(track)
                        else:
                            abort(404)
                            
                    # No track specified, try to play the last "single" track    
                    elif(player.currently_playing != None) and (len(player.current_playlist)==0):
                            
                        #play the active track
                        player.load_and_play(player.currently_playing)  
                        
                    
                # check playlist if any
                elif "playlist" in play_request:
                    # no multiple playlist supported...just play it
                    
                    # get the playlist
                    playlist = play_request["playlist"];
                   
                    # check for tracks in the playlist
                    if (playlist!="") and (playlist["tracks"] != None):
                        
                        # prepare the playlist holding full track information
                        full_playlist = []
                        
                        # for all tracks
                        for track in playlist["tracks"]:
                            
                            # get the track
                            full_track_data = track_list.get_track(int(track))
                            
                            # if valid add to the play list
                            if(full_track_data != None):
                                # add the track
                                full_playlist.append(full_track_data)
                            
                        if(len(full_playlist) > 0):
                            # switch playlist
                            player.load_playlist(full_playlist)
                        else:
                            abort(404) 
                            
                    #nothing specified: try to play the last playlist, if available            
                    elif len(player.current_playlist) > 0:
                        
                        # play existing playlist
                        if(player.currently_playing_id < len(player.current_playlist)):
                            
                            # get the current id
                            target_id = player.currently_playing_id
                            
                            # get the current playlist
                            target_playlist = [track for track in player.current_playlist]
                            
                            # reschedule track playing
                            player.load_playlist(target_playlist)
                            
                            # skip to the right track
                            while (player.currently_playing_id != target_id):
                                player.next()
                        else:
                            # load and start from the beginning
                            player.load_playlist(player.current_playlist)  
                    
            # STOP  
            elif command.lower() == 'stop':
                # stop playing
                player.stop()
            # NEXT
            elif command.lower() == 'next':
                # skip to next track
                if(len(player.current_playlist) > 0):
                    player.next()
                else:
                    abort(404)
        except:
            pass
            
        # handle currently playing tracks, in particular the empty case
        if(player.currently_playing == None):
            current = "No track"
        else:
            current = player.currently_playing.jsonifiable()
            
        return  jsonify({"status":player.status, "current" : current, "queue":[track.jsonifiable() for track in player.current_playlist[(player.currently_playing_id + 1):] if track != None]})
    
    # no command -> abort
    abort(404)

@app.route('/music/api/v1.0/player', methods=['GET'])
def getStatus():
    # handle currently playing tracks, in particular the empty case
    if(player.currently_playing == None):
        current = "No track"
    else:
        current = player.currently_playing.jsonifiable()
    
    #return the status        
    return  jsonify({"status":player.status, "current" : current, "queue":[track.jsonifiable() for track in player.current_playlist[(player.currently_playing_id + 1):] if track != None]})


def usage():
    print "Flask Music Server"
    print "Usage: flask_music_server.py [-h help][-d music-folder]"

if __name__ == '__main__':
    # parse arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:d:", ["help", "music_dir="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err)  # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
        
    # handle command-line options
    for o, a in opts:
        # handle help
        if o in ("-h", "--help"):
            
            # show usage
            usage()
            
            # exit with success code
            sys.exit(0)
            
        # handle configuration data
        elif o in ("-d", "--music_dir"):
                        
            # initialize the track list
            track_list = TrackList()
            
            # player
            player = Player()
            
            # initialize the available tracks
            track_list.add_tracks(track_list.scan(a))
            
            # initializa the album list
            album_list = AlbumList()
            
            # extract the available albums
            album_list.from_tracklist(track_list.tracks)
    
            # run flask
            app.run(debug=True)
        else:
            usage()
            sys.exit(-1)
            
if(player == None):
    print("Not enough parameters to run...")
    usage()
