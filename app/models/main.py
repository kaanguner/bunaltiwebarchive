# app/views/main.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from sqlalchemy import func, desc # Import desc for ordering
from sqlalchemy import or_ # Import 'or_' for case-insensitive search if needed, though ILIKE handles it


# Import models needed for these routes
# Assuming your models are correctly defined in these files within app/models/
from app.models.user_stats import UserStats
from app.models.post import Post
from app.models.comment import Comment
from app import db # Import the database instance initialized in app/__init__.py

# --- Blueprint Definition ---
# Create a Blueprint instance named 'main'.
# The first argument 'main' is the blueprint's name used internally by Flask (e.g., in url_for).
# The second argument __name__ helps Flask locate the blueprint's root path.
# template_folder='../templates' tells Flask to look for templates in the directory
# one level up from the current directory (views/), which is the app/templates/ folder.
bp = Blueprint('main', __name__, template_folder='../templates')

# --- Route Definitions ---

@bp.route('/')
def index():
    """Renders the homepage."""
    try:
        # Query top users based on comment count
        top_users = UserStats.query.order_by(UserStats.total_comments.desc()).limit(10).all()
    except Exception as e:
        # Log the error and show an empty list if the query fails
        print(f"Error fetching top users: {e}")
        flash("Could not retrieve user statistics at the moment.", "warning")
        top_users = []

    # Render the index.html template, passing the title and users
    return render_template('index.html', title='Home', top_users=top_users)

@bp.route('/search')
def search():
    """Handles the username search form submission."""
    # Get the username from the query string, strip whitespace
    username = request.args.get('username', '', type=str).strip()

    # Validate input
    if not username:
        flash('Please enter a username to search.', 'warning')
        return redirect(url_for('main.index')) # Redirect back to homepage

    try:
        # Check if a user with this username exists in the UserStats table
        # .get() is efficient for primary key lookups
        user = UserStats.query.get(username)
    except Exception as e:
        print(f"Error searching for user '{username}': {e}")
        flash("An error occurred while searching for the user.", "danger")
        return redirect(url_for('main.index'))

    # If user exists, redirect to their profile page
    if user:
        return redirect(url_for('main.user_profile', username=username))
    # If user doesn't exist, show a message and redirect back to homepage
    else:
        flash(f'Username "{username}" not found in the archive.', 'info')
        return redirect(url_for('main.index'))

@bp.route('/user/<username>')
def user_profile(username):
    """Displays the user profile page with their stats and participated threads."""
    try:
        # Fetch user statistics or return a 404 error if not found
        user_stats = UserStats.query.get_or_404(username)

        # Query to get:
        # 1. The Post object
        # 2. The count of comments made by *this specific user* on that post
        # It joins Post and Comment tables, filters by the username,
        # groups by the Post to count comments per post, and orders the results.
        threads_participated = db.session.query(
                Post,
                func.count(Comment.id).label('user_comment_count') # Count comments and label the result
            ).join(Comment, Post.id == Comment.post_id)\
            .filter(Comment.author == username)\
            .group_by(Post.id)\
            .order_by(desc(Post.timestamp))\
            .all() # Fetch all matching threads
    except Exception as e:
        print(f"Error fetching profile data for '{username}': {e}")
        flash("An error occurred while retrieving the user profile.", "danger")
        # Redirect to homepage or show a generic error page
        return redirect(url_for('main.index'))

    # Render the user_profile.html template, passing the necessary data
    return render_template('user_profile.html',
                           title=f"{username}'s Profile",
                           user_stats=user_stats,
                           threads=threads_participated)

@bp.route('/thread/<int:post_id>')
def thread_view(post_id):
    """Displays a specific thread (post and its comments)."""
    try:
        # Fetch the specific post or return 404 if not found
        post = Post.query.get_or_404(post_id)

        # Fetch all comments associated with this post, ordered by ID (or comment_number if reliable)
        comments = Comment.query.filter_by(post_id=post.id).order_by(Comment.id).all()

        # Get the username to highlight from the query string (?highlight_user=...)
        highlight_user = request.args.get('highlight_user', None) # Get from URL parameter

    except Exception as e:
        print(f"Error fetching thread data for post ID {post_id}: {e}")
        flash("An error occurred while retrieving the thread.", "danger")
        return redirect(url_for('main.index'))

    # --- THIS IS THE REAL RENDER CALL ---
    # Render the thread.html template, passing the necessary data
    return render_template('thread.html',
                           title=post.title, # Set the page title
                           post=post,        # Pass the Post object
                           comments=comments,  # Pass the list of Comment objects
                           highlight_user=highlight_user) # Pass the username to highlight

@bp.route('/search/threads')
def thread_search():
    """Handles searching for posts based on title keywords."""
    query = request.args.get('q', '').strip() # Get search query from 'q' parameter

    if not query:
        flash('Please enter keywords to search for in thread titles.', 'warning')
        return redirect(url_for('main.index')) # Redirect if query is empty

    print(f"Searching for threads with title containing: '{query}'") # For debugging

    try:
        # Perform a case-insensitive search using ILIKE
        search_term = f"%{query}%" # Add wildcards for substring matching
        # Find posts where the title contains the query term
        results = Post.query.filter(
            Post.title.ilike(search_term)
        ).order_by(
            desc(Post.timestamp) # Order by timestamp descending (newest first)
        ).limit(100).all() # Limit results to avoid overwhelming page
        # Consider adding pagination later if results can be very large

        result_count = len(results)
        print(f"Found {result_count} matching posts.") # For debugging

    except Exception as e:
        print(f"Error during thread search for '{query}': {e}")
        flash("An error occurred while searching for threads.", "danger")
        results = []
        result_count = 0

    # Render a new template to display results
    return render_template('search_results.html',
                           title=f"Search Results for '{query}'",
                           query=query,
                           results=results,
                           result_count=result_count)