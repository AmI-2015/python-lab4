'''
Music utilities, provides the core classes needed to implement a simple music server, 
possibly including playlist handling.
Created on Apr 13, 2015

@author: bonino
'''
from mutagen import flac, mp3
from subprocess import Popen, PIPE

import os

#----- Classes -------------

class Track:
    '''
    A class representing a music file
    '''
    
    def __init__(self, path=None):
        
        # the track id
        self.id = None
        
        # the file to which the track points (full path)
        self.path = path
        
        # extract the track description from file tags
        self.data = self.metadata() 
        
    
    def metadata(self):
        
        track_data = {}
        
        # default name
        track_data['title'] = self.path[:self.path.rfind('.')]
        track_data['album'] = None
        track_data['genre'] = None
        track_data['artist'] = None
        
        # detect the current file type
        file_type = self.path[self.path.rfind('.'):]
        
        # handle FLAC files
        if file_type == ".flac":
            metadata = flac.FLAC(self.path)
            # print metadata
            try:
                track_data['title'] = metadata['title'][0]
                track_data['album'] = metadata['album'][0]
                track_data['genre'] = metadata['genre'][0]
                track_data['artist'] = metadata['artist'][0]
            except:
                pass
        # handle MP3 files
        if file_type == ".mp3":
            metadata = mp3.MP3(self.path)
            # print metadata
            try:
                if(metadata.has_key('TIT2')):
                    track_data['title'] = metadata['TIT2'].text[0]
                if(metadata.has_key('TALB')):
                    track_data['album'] = metadata['TALB'].text[0]
                if(metadata.has_key('TCON')):
                    track_data['genre'] = metadata['TCON'].text[0]
                if(metadata.has_key('TPE2')):
                    track_data['artist'] = metadata['TPE2'].text[0]
            except:
                pass
        
        return track_data
    
    def jsonifiable(self):
        track = {}
        track['id'] = self.id
        track['path'] = self.path
        track['metadata'] = self.data
        
        return track
    
    
class TrackList:
    '''
    A class representing a "list" of music files
    '''
    def __init__(self):
        
        # the list
        self.tracks = []
        
        # the last index
        self.lastId = 0
    
    def scan(self, root_folder):
        '''
        Walks the given directory to find mp3 and flac music files
        '''
        # the tracks in the given (root) folder...
        tracks_in_folder = []
        
        # track counter
        i = 0
        
        # iterate over subdirectories, following symlinks
        for directory in os.walk(root_folder, followlinks=True):
            # for each file in the current directory            
            for filename in directory[2]:
                # check the file extension
                if filename.endswith('.mp3') or filename.endswith('.flac'):
                    # set the track file path
                    current_track = Track(os.path.join(directory[0], filename))
                    
                    # debug
                    print (current_track.path)
                    
                    # set the track id, not unique:may change between different runs
                    current_track.id = i;
                    
                    # append the current track
                    tracks_in_folder.append(current_track)
                    
                    # increment the track id
                    i += 1
        return tracks_in_folder
                    
    def add_tracks(self, tracks, auto_id=True):
        '''
        Adds the given (set) of tracks. 
        '''
        for track in tracks:
            # reset the track id
            if(auto_id):
                track.id = self.lastId
                self.lastId += 1
            # appedn the track
            self.tracks.append(track)
            
    def get_track(self, track_id):
        
        # the track to return
        track = None
        
        # get the track info
        found_tracks = [trackz for trackz in self.tracks if trackz.id == track_id]
        
        # return the track info
        if(len(found_tracks) > 0):
            track = found_tracks[0]
        
        return track
                
    def search(self, filter_parameters):
        '''
        Searches for tracks having / containing the given value in the given tag
        '''
        
        # the list of matching tracks
        matching_tracks = []
        
        # check if parameters are available
        if filter_parameters != None:
            
            # iterate over all available tracks
            for track in self.tracks:
                
                try:
                    #implement AND
                    matching_params = 0
                    
                    for param in filter_parameters:
                        
                        # the track param
                        track_field = track.data[param]
                        
                        # apply filter
                        if (track_field != None) and ((track_field.lower() == filter_parameters[param].lower()) or (track_field.lower().find(filter_parameters[param].lower()) > -1)):  
                            matching_params = matching_params+1
                    
                    if(matching_params == len(filter_parameters)) and (len([trackz for trackz in matching_tracks if trackz.id == track.id]) == 0):    
                        # if the filter matches, add the track
                        matching_tracks.append(track)
                except:
                    #skip silently
                    pass
            
        # return the set of matching tracks
        return matching_tracks

class Album:
    def __init__(self, artist = None, title = None, tracks = None):
        #the album id
        self.id = 0
        
        #the artist
        self.artist = artist
        #title
        self.title = title
        #tracks
        self.track_list = TrackList()
    
    def add_tracks(self,tracks):
        # append the track
        self.track_list.add_tracks(tracks, False)
    
    def jsonifiable(self):
        #prepare the album dictionary
        album = {}
        
        #the id
        album['id'] = self.id
        
        # the artist
        album['artist'] = self.artist
        
        # the title
        album['title'] = self.title
        
        # the list of tracks
        album['tracks'] =  [track.jsonifiable() for track in self.track_list.tracks]
        
        return album
        
class AlbumList:
    def __init__(self):
        
        #the first free id
        self.last_id = 0;
        
        #the album array
        self.albums = []
    
    def from_tracklist(self, tracklist):
        #check not None
        if (tracklist!= None):
            for track in tracklist:
                #check if the album already exist
                album = self.get_album_by_name(track.data['album'])
                if(album == None):
                    #create the album
                    album = Album(title = track.data['album'], artist = track.data['artist'])
                    
                    #set the album id
                    album.id = self.last_id
                    self.last_id = self.last_id+1
                    
                    #add the album
                    self.albums.append(album)
    
                #add the track
                album.add_tracks({track})
                
    def get_album_by_name(self, name):
        #the actual album to return
        album = None
        
        #get the album having the given name 
        found_albums = [albumz for albumz in self.albums if albumz.title == name]
        
        #if at least one album matches, get the first
        if(len(found_albums)>0):
            album = found_albums[0]
        
        #return the album found
        return album
    
    def get_album(self, album_id):
        #the album to return
        album = None
        
        #get the album having the given id
        found_albums = [albumz for albumz in self.albums if albumz.id == album_id]
        
        #if at least one album matches get the first
        if(len(found_albums)>0):
            album = found_albums[0]
        
        #return the album found
        return album 
                    
            
        
class Player:
    def __init__(self):
        # the tracklist
        self.current_playlist = []
        
        # the currently playing list
        self.currently_playing = None
        self.currently_playing_id = -1
        
        # the player status
        self.status = "stopped"
        
        # build the player
        self.player = Popen("mplayer -slave -quiet -nolirc -msglevel all=-1 -idle", stdin=PIPE, stdout=PIPE, shell=True)          
       
    def load_and_play(self, track):
        
        # clear any playlist
        self.current_playlist = []
        
        # play the file
        self.player.stdin.write("loadfile \"%s\"\n" % track.path)   
        
        # set the currently playing track
        self.currently_playing = track
        self.currently_playing_id = -1
        
        # update the player status
        self.status = "playing"       

    def next(self):
        # skip to next track
        self.player.stdin.write("pt_step 1\n")
        
        # handle queue composition
        if(len(self.current_playlist) > 0):
            # the next id
            next_id = self.currently_playing_id + 1
            
            if(len(self.current_playlist) > next_id):
                # update the current track
                self.currently_playing = self.current_playlist[next_id]
                self.currently_playing_id = next_id
            else:
                # stop playing
                self.stop()
                
                # reset playlist
                self.currently_playing_id = 0
                self.currently_playing = self.current_playlist[self.currently_playing_id]
                
                # update the player status
                self.status = "stopped"
        
            
                
    
    def stop(self):
        # stop playing
        self.player.stdin.write("stop\n") 
        
        # update the player status
        self.status = "stopped"
        
    def exit(self):
        # quit the player
        self.player.stdin.write("quit\n") 
    
    def load_playlist(self, tracks):
        # initialize the playlist track counter
        i = 0    
        
        # initialize the play list
        self.current_playlist = []
        
        for track in tracks:
            # add the track to the current playlist
            self.current_playlist.append(track)
            
            # start playing the first track 
            if(i == 0):
                self.player.stdin.write("loadfile \"%s\"\n" % track.path)
                # update the inner status
                self.status = "playing"
                self.currently_playing = track
                self.currently_playing_id = 0
                
                # update the player status
                self.status = "playing"
            else:
                # enqueue
                self.player.stdin.write("loadfile \"%s\" %s\n" % (track.path, i))

            # increment track counter
            i += 1
            
