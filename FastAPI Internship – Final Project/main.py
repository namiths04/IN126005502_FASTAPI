from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI(title="CineStar Movie Ticket Booking")

# --- DATASETS ---
movies = [
    {"id": 1, "title": "Inception", "genre": "Sci-Fi", "language": "English", "duration_mins": 148, "ticket_price": 250, "seats_available": 10},
    {"id": 2, "title": "The Dark Knight", "genre": "Action", "language": "English", "duration_mins": 152, "ticket_price": 300, "seats_available": 5},
    {"id": 3, "title": "Interstellar", "genre": "Sci-Fi", "language": "English", "duration_mins": 169, "ticket_price": 280, "seats_available": 8},
    {"id": 4, "title": "Parasite", "genre": "Thriller", "language": "Korean", "duration_mins": 132, "ticket_price": 220, "seats_available": 12},
    {"id": 5, "title": "Avengers", "genre": "Action", "language": "English", "duration_mins": 181, "ticket_price": 350, "seats_available": 0},
    {"id": 6, "title": "Kantara", "genre": "Drama", "language": "Kannada", "duration_mins": 148, "ticket_price": 180, "seats_available": 20},
]
bookings, holds = [], []
booking_counter, hold_counter = 1, 1

# --- MODELS ---
class BookingRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    movie_id: int = Field(..., gt=0)
    seats: int = Field(..., gt=0, le=10)
    phone: str = Field(..., min_length=10)
    seat_type: str = "standard"
    promo_code: Optional[str] = ""

class NewMovie(BaseModel):
    title: str = Field(..., min_length=2)
    genre: str = Field(..., min_length=2)
    language: str = Field(..., min_length=2)
    duration_mins: int = Field(..., gt=0)
    ticket_price: int = Field(..., gt=0)
    seats_available: int = Field(..., gt=0)

# --- HELPERS ---
def find_movie(movie_id: int):
    return next((m for m in movies if m["id"] == movie_id), None)

# --- ROUTES ---

@app.get("/")
async def home(): 
    return {"message": "Welcome to CineStar"}

# Q16 & Q17: Search by Keyword and Pagination
@app.get("/movies/search")
async def search_movies(
    keyword: str = Query(..., min_length=1), 
    page: int = 1, 
    limit: int = 2
):
    results = [m for m in movies if keyword.lower() in m["title"].lower()]
    start = (page - 1) * limit
    end = start + limit
    return {
        "keyword": keyword,
        "page": page,
        "limit": limit,
        "total_results": len(results),
        "movies": results[start:end]
    }

@app.get("/movies")
async def get_movies(): 
    return {"movies": movies}

@app.get("/movies/summary")
async def get_summary():
    prices = [m["ticket_price"] for m in movies]
    return {"total_movies": len(movies), "max_price": max(prices), "min_price": min(prices)}

@app.get("/movies/filter")
async def filter_movies(genre: Optional[str] = None, max_price: Optional[int] = None):
    results = movies
    if genre:
        results = [m for m in results if m["genre"].lower() == genre.lower()]
    if max_price:
        results = [m for m in results if m["ticket_price"] <= max_price]
    return {"movies": results}

@app.get("/movies/{movie_id}")
async def get_movie(movie_id: int):
    movie = find_movie(movie_id)
    return movie if movie else {"error": "Not found"}

# Q12: Partial Update Route (PATCH)
@app.patch("/movies/{movie_id}")
async def update_movie(movie_id: int, ticket_price: Optional[int] = None, seats: Optional[int] = None):
    movie = find_movie(movie_id)
    if not movie: raise HTTPException(status_code=404, detail="Movie not found")
    if ticket_price: movie["ticket_price"] = ticket_price
    if seats is not None: movie["seats_available"] = seats
    return movie

@app.post("/movies", status_code=status.HTTP_201_CREATED)
async def add_movie(movie: NewMovie):
    new_id = max(m["id"] for m in movies) + 1
    new_movie = {"id": new_id, **movie.model_dump()}
    movies.append(new_movie)
    return new_movie

@app.delete("/movies/{movie_id}")
async def delete_movie(movie_id: int):
    movie = find_movie(movie_id)
    if not movie: raise HTTPException(status_code=404)
    movies.remove(movie)
    return {"message": f"Movie '{movie['title']}' deleted"}

@app.post("/bookings", status_code=status.HTTP_201_CREATED)
async def create_booking(request: BookingRequest):
    movie = find_movie(request.movie_id)
    if not movie or movie["seats_available"] < request.seats:
        raise HTTPException(status_code=400, detail="Invalid request")
    movie["seats_available"] -= request.seats
    global booking_counter
    new_booking = {"booking_id": booking_counter, **request.model_dump()}
    bookings.append(new_booking)
    booking_counter += 1
    return new_booking

@app.post("/seat-hold")
async def hold_seats(customer_name: str, movie_id: int, seats: int):
    movie = find_movie(movie_id)
    if not movie or movie["seats_available"] < seats: raise HTTPException(status_code=400)
    global hold_counter
    movie["seats_available"] -= seats
    new_hold = {"hold_id": hold_counter, "customer_name": customer_name, "movie_id": movie_id, "seats": seats}
    holds.append(new_hold)
    hold_counter += 1
    return new_hold

@app.post("/seat-confirm/{hold_id}")
async def confirm_hold(hold_id: int):
    hold = next((h for h in holds if h["hold_id"] == hold_id), None)
    if not hold: raise HTTPException(status_code=404)
    global booking_counter
    confirmed = {"booking_id": booking_counter, **hold, "status": "confirmed"}
    bookings.append(confirmed)
    booking_counter += 1
    holds.remove(hold)
    return confirmed