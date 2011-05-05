# Copyright (C) 2010, 2011 Sebastian Thiel (byronimo@gmail.com) and contributors
#
# This module is part of GitDB and is released under
# the New BSD License: http://www.opensource.org/licenses/bsd-license.php
"""Contains interfaces for basic database building blocks"""

__all__ = (	'ObjectDBR', 'ObjectDBW', 'RootPathDB', 'CompoundDB', 'CachingDB', 
			'TransportDB', 'ConfigurationMixin', 'RepositoryPathsMixin',  
			'RefSpec', 'FetchInfo', 'PushInfo', 'ReferencesMixin')


class ObjectDBR(object):
	"""Defines an interface for object database lookup.
	Objects are identified either by their 20 byte bin sha"""
	
	def __contains__(self, sha):
		return self.has_obj(sha)
	
	#{ Query Interface 
	def has_object(self, sha):
		"""
		:return: True if the object identified by the given 20 bytes
			binary sha is contained in the database"""
		raise NotImplementedError("To be implemented in subclass")
		
	def has_object_async(self, reader):
		"""Return a reader yielding information about the membership of objects
		as identified by shas
		:param reader: Reader yielding 20 byte shas.
		:return: async.Reader yielding tuples of (sha, bool) pairs which indicate
			whether the given sha exists in the database or not"""
		raise NotImplementedError("To be implemented in subclass")
		
	def info(self, sha):
		""" :return: OInfo instance
		:param sha: bytes binary sha
		:raise BadObject:"""
		raise NotImplementedError("To be implemented in subclass")
		
	def info_async(self, reader):
		"""Retrieve information of a multitude of objects asynchronously
		:param reader: Channel yielding the sha's of the objects of interest
		:return: async.Reader yielding OInfo|InvalidOInfo, in any order"""
		raise NotImplementedError("To be implemented in subclass")
		
	def stream(self, sha):
		""":return: OStream instance
		:param sha: 20 bytes binary sha
		:raise BadObject:"""
		raise NotImplementedError("To be implemented in subclass")
		
	def stream_async(self, reader):
		"""Retrieve the OStream of multiple objects
		:param reader: see ``info``
		:param max_threads: see ``ObjectDBW.store``
		:return: async.Reader yielding OStream|InvalidOStream instances in any order
		:note: depending on the system configuration, it might not be possible to 
			read all OStreams at once. Instead, read them individually using reader.read(x)
			where x is small enough."""
		raise NotImplementedError("To be implemented in subclass")
	
	def size(self):
		""":return: amount of objects in this database"""
		raise NotImplementedError()
		
	def sha_iter(self):
		"""Return iterator yielding 20 byte shas for all objects in this data base"""
		raise NotImplementedError()
		
	def partial_to_complete_sha_hex(self, partial_hexsha):
		"""
		:return: 20 byte binary sha1 from the given less-than-40 byte hexsha
		:param partial_hexsha: hexsha with less than 40 byte
		:raise AmbiguousObjectName: If multiple objects would match the given sha 
		:raies BadObject: If object was not found"""
		raise NotImplementedError()
			
	def partial_to_complete_sha(self, partial_binsha, canonical_length):
		""":return: 20 byte sha as inferred by the given partial binary sha
		:param partial_binsha: binary sha with less than 20 bytes 
		:param canonical_length: length of the corresponding canonical (hexadecimal) representation.
			It is required as binary sha's cannot display whether the original hex sha
			had an odd or even number of characters
		:raise AmbiguousObjectName: 
		:raise BadObject: """
	#} END query interface
	
	
class ObjectDBW(object):
	"""Defines an interface to create objects in the database"""
	
	#{ Edit Interface
	def set_ostream(self, stream):
		"""
		Adjusts the stream to which all data should be sent when storing new objects
		
		:param stream: if not None, the stream to use, if None the default stream
			will be used.
		:return: previously installed stream, or None if there was no override
		:raise TypeError: if the stream doesn't have the supported functionality"""
		raise NotImplementedError("To be implemented in subclass")
		
	def ostream(self):
		"""
		:return: overridden output stream this instance will write to, or None
			if it will write to the default stream"""
		raise NotImplementedError("To be implemented in subclass")
	
	def store(self, istream):
		"""
		Create a new object in the database
		:return: the input istream object with its sha set to its corresponding value
		
		:param istream: IStream compatible instance. If its sha is already set 
			to a value, the object will just be stored in the our database format, 
			in which case the input stream is expected to be in object format ( header + contents ).
		:raise IOError: if data could not be written"""
		raise NotImplementedError("To be implemented in subclass")
	
	def store_async(self, reader):
		"""
		Create multiple new objects in the database asynchronously. The method will 
		return right away, returning an output channel which receives the results as 
		they are computed.
		
		:return: Channel yielding your IStream which served as input, in any order.
			The IStreams sha will be set to the sha it received during the process, 
			or its error attribute will be set to the exception informing about the error.
			
		:param reader: async.Reader yielding IStream instances.
			The same instances will be used in the output channel as were received
			in by the Reader.
		
		:note:As some ODB implementations implement this operation atomic, they might 
			abort the whole operation if one item could not be processed. Hence check how 
			many items have actually been produced."""
		raise NotImplementedError("To be implemented in subclass")
	
	#} END edit interface
	

class RootPathDB(object):
	"""Provides basic facilities to retrieve files of interest"""
	
	def __init__(self, root_path):
		"""Initialize this instance to look for its files at the given root path
		All subsequent operations will be relative to this path
		:raise InvalidDBRoot: 
		:note: The base will not perform any accessablity checking as the base
			might not yet be accessible, but become accessible before the first 
			access."""
		super(RootPathDB, self).__init__(root_path)
		
	#{ Interface 
	def root_path(self):
		""":return: path at which this db operates"""
		raise NotImplementedError()
	
	def db_path(self, rela_path):
		"""
		:return: the given relative path relative to our database root, allowing 
			to pontentially access datafiles"""
		raise NotImplementedError()
	#} END interface
		

class CachingDB(object):
	"""A database which uses caches to speed-up access"""
	
	#{ Interface 
	
	def update_cache(self, force=False):
		"""
		Call this method if the underlying data changed to trigger an update
		of the internal caching structures.
		
		:param force: if True, the update must be performed. Otherwise the implementation
			may decide not to perform an update if it thinks nothing has changed.
		:return: True if an update was performed as something change indeed"""
		
	# END interface

class CompoundDB(object):
	"""A database which delegates calls to sub-databases.
	They should usually be cached and lazy-loaded"""
	
	#{ Interface
	
	def databases(self):
		""":return: tuple of database instances we use for lookups"""
		raise NotImplementedError()

	#} END interface
	

class RefSpec(object):
	"""A refspec is a simple container which provides information about the way
	something should be fetched or pushed. It requires to use symbols to describe
	the actual objects which is done using reference names (or respective instances
	which resolve to actual reference names)."""
	__slots__ = ('source', 'destination', 'force')
	
	def __init__(self, source, destination, force=False):
		"""initalize the instance with the required values
		:param source: reference name or instance. If None, the Destination 
			is supposed to be deleted."""
		self.source = source
		self.destination = destination
		self.force = force
		if self.destination is None:
			raise ValueError("Destination must be set")
		
	def __str__(self):
		""":return: a git-style refspec"""
		s = str(self.source)
		if self.source is None:
			s = ''
		#END handle source
		d = str(self.destination)
		p = ''
		if self.force:
			p = '+'
		#END handle force
		res = "%s%s:%s" % (p, s, d)
		
	def delete_destination(self):
		return self.source is None
		
		
class PushInfo(object):
	"""A type presenting information about the result of a push operation for exactly
	one refspec

	flags				# bitflags providing more information about the result
	local_ref			# Reference pointing to the local reference that was pushed
						# It is None if the ref was deleted.
	remote_ref_string 	# path to the remote reference located on the remote side
	remote_ref 			# Remote Reference on the local side corresponding to 
						# the remote_ref_string. It can be a TagReference as well.
	old_commit 			# commit at which the remote_ref was standing before we pushed
						# it to local_ref.commit. Will be None if an error was indicated
	summary				# summary line providing human readable english text about the push
	"""
	__slots__ = tuple()
	
	NEW_TAG, NEW_HEAD, NO_MATCH, REJECTED, REMOTE_REJECTED, REMOTE_FAILURE, DELETED, \
	FORCED_UPDATE, FAST_FORWARD, UP_TO_DATE, ERROR = [ 1 << x for x in range(11) ]
		
		
class FetchInfo(object):
	"""A type presenting information about the fetch operation on exactly one refspec
	
	The following members are defined:
	ref				# name of the reference to the changed 
					# remote head or FETCH_HEAD. Implementations can provide
					# actual class instance which convert to a respective string
	flags			# additional flags to be & with enumeration members, 
					# i.e. info.flags & info.REJECTED 
					# is 0 if ref is FETCH_HEAD
	note				# additional notes given by the fetch-pack implementation intended for the user
	old_commit		# if info.flags & info.FORCED_UPDATE|info.FAST_FORWARD, 
					# field is set to the previous location of ref as hexsha or None
					# Implementors may use their own type too, but it should decay into a
					# string of its hexadecimal sha representation"""
	__slots__ = tuple()
	
	NEW_TAG, NEW_HEAD, HEAD_UPTODATE, TAG_UPDATE, REJECTED, FORCED_UPDATE, \
	FAST_FORWARD, ERROR = [ 1 << x for x in range(8) ]


class TransportDB(object):
	"""A database which allows to transport objects from and to different locations
	which are specified by urls (location) and refspecs (what to transport, 
	see http://www.kernel.org/pub/software/scm/git/docs/git-fetch.html).
	
	At the beginning of a transport operation, it will be determined which objects
	have to be sent (either by this or by the other side).
	
	Afterwards a pack with the required objects is sent (or received). If there is 
	nothing to send, the pack will be empty.
	
	As refspecs involve symbolic names for references to be handled, we require
	RefParse functionality. How this is done is up to the actual implementation."""
	# The following variables need to be set by the derived class
	
	#{ Interface
	
	def fetch(self, url, refspecs, progress=None, **kwargs):
		"""Fetch the objects defined by the given refspec from the given url.
		:param url: url identifying the source of the objects. It may also be 
			a symbol from which the respective url can be resolved, like the
			name of the remote. The implementation should allow objects as input
			as well, these are assumed to resovle to a meaningful string though.
		:param refspecs: iterable of reference specifiers or RefSpec instance, 
			identifying the references to be fetch from the remote.
		:param progress: callable which receives progress messages for user consumption
		:param kwargs: may be used for additional parameters that the actual implementation could 
			find useful.
		:return: List of FetchInfo compatible instances which provide information about what 
			was previously fetched, in the order of the input refspecs.
		:note: even if the operation fails, one of the returned FetchInfo instances
			may still contain errors or failures in only part of the refspecs.
		:raise: if any issue occours during the transport or if the url is not 
			supported by the protocol.
		"""
		raise NotImplementedError()
		
	def push(self, url, refspecs, progress=None, **kwargs):
		"""Transport the objects identified by the given refspec to the remote
		at the given url.
		:param url: Decribes the location which is to receive the objects
			see fetch() for more details
		:param refspecs: iterable of refspecs strings or RefSpec instances
			to identify the objects to push
		:param progress: see fetch() 
		:param kwargs: additional arguments which may be provided by the caller
			as they may be useful to the actual implementation
		:todo: what to return ?
		:raise: if any issue arises during transport or if the url cannot be handled"""
		raise NotImplementedError()
		
	@property
	def remotes(self):
		""":return: An IterableList of Remote objects allowing to access and manipulate remotes
		:note: Remote objects can also be used for the actual push or fetch operation"""
		raise NotImplementedError()
		
	#}end interface


class ReferencesMixin(object):
	"""Database providing reference objects which in turn point to database objects
	like Commits or Tag(Object)s.
	
	The returned types are compatible to the interfaces of the pure python 
	reference implementation in GitDB.ref"""
	
	def resolve(self, name):
		"""Resolve the given name into a binary sha. Valid names are as defined 
		in the rev-parse documentation http://www.kernel.org/pub/software/scm/git/docs/git-rev-parse.html
		:return: binary sha matching the name
		:raise AmbiguousObjectName:
		:raise BadObject: """
		raise NotImplementedError()
	
	@property
	def references(self):
		""":return: iterable list of all Reference objects representing tags, heads
		and remote references. This is the most general method to obtain any 
		references."""
		raise NotImplementedError()
		
	@property
	def heads(self):
		""":return: IterableList with HeadReference objects pointing to all
		heads in the repository."""
		raise NotImplementedError()
		
	@property
	def tags(self):
		""":return: An IterableList of TagReferences that are available in this repo"""
		raise NotImplementedError()
		
		
class RepositoryPathsMixin(object):
	"""Represents basic functionality of a full git repository. This involves an 
	optional working tree, a git directory with references and an object directory.
	
	This type collects the respective paths and verifies the provided base path 
	truly is a git repository.
	
	If the underlying type provides the config_reader() method, we can properly determine 
	whether this is a bare repository as well. Otherwise it will make an educated guess
	based on the path name."""
	#{ Subclass Interface
	def _initialize(self, path):
		"""initialize this instance with the given path. It may point to 
		any location within the repositories own data, as well as the working tree.
		
		The implementation will move up and search for traces of a git repository, 
		which is indicated by a child directory ending with .git or the 
		current path portion ending with .git.
		
		The paths made available for query are suitable for full git repositories
		only. Plain object databases need to be fed the "objects" directory path.
		
		:param path: the path to initialize the repository with
		:raise InvalidDBRoot:
		"""
		raise NotImplementedError()
	#} end subclass interface
	
	#{ Interface
	
	def is_bare(self):
		""":return: True if this is a bare repository
		:note: this value is cached upon initialization"""
		raise NotImplementedError()
		
	def git_path(self):
		""":return: path to directory containing this actual git repository (which 
		in turn provides access to objects and references"""
		raise NotImplementedError()
		
	def working_tree_path(self):
		""":return: path to directory containing the working tree checkout of our 
		git repository.
		:raise AssertionError: If this is a bare repository"""
		raise NotImplementedError()
		
	def objects_path(self):
		""":return: path to the repository's objects directory"""
		raise NotImplementedError()
		
	def working_dir(self):
		""":return: working directory of the git process or related tools, being 
		either the working_tree_path if available or the git_path"""
		raise NotImplementedError()
		
	#} END interface
		
		
class ConfigurationMixin(object):
	"""Interface providing configuration handler instances, which provide locked access
	to a single git-style configuration file (ini like format, using tabs as improve readablity).
	
	Configuration readers can be initialized with multiple files at once, whose information is concatenated
	when reading. Lower-level files overwrite values from higher level files, i.e. a repository configuration file 
	overwrites information coming from a system configuration file
	
	:note: for the 'repository' config level, a git_path() compatible type is required"""
	config_level = ("system", "global", "repository")
		
	#{ Interface
	
	def config_reader(self, config_level=None):
		"""
		:return:
			GitConfigParser allowing to read the full git configuration, but not to write it
			
			The configuration will include values from the system, user and repository 
			configuration files.
			
		:param config_level:
			For possible values, see config_writer method
			If None, all applicable levels will be used. Specify a level in case 
			you know which exact file you whish to read to prevent reading multiple files for 
			instance
		:note: On windows, system configuration cannot currently be read as the path is 
			unknown, instead the global path will be used."""
		raise NotImplementedError()
		
	def config_writer(self, config_level="repository"):
		"""
		:return:
			GitConfigParser allowing to write values of the specified configuration file level.
			Config writers should be retrieved, used to change the configuration ,and written 
			right away as they will lock the configuration file in question and prevent other's
			to write it.
			
		:param config_level:
			One of the following values
			system = sytem wide configuration file
			global = user level configuration file
			repository = configuration file for this repostory only"""
		raise NotImplementedError()
	
	#} END interface
	
