from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Annotated
from sqlalchemy.orm import Session
import models
from database import SessionLocal, engine
import bcrypt
import uvicorn  # Add this import

app = FastAPI()
models.Base.metadata.create_all(bind=engine)

# Models
class PostBase(BaseModel):
    title: str
    content: str
    user_id: int

class UserBase(BaseModel):
    username: str
    password: str  # Use plain text password here, not hashed_password

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

# Post creation
@app.post("/posts/", status_code=status.HTTP_201_CREATED)
async def create_post(post: PostBase, db: db_dependency):
    db_post = models.Post(**post.dict())
    db.add(db_post)
    db.commit()
    return db_post

# Read post by ID
@app.get("/posts/{post_id}", status_code=status.HTTP_200_OK)
async def read_post(post_id: int, db: db_dependency):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# Delete post by ID
@app.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: db_dependency):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    db.delete(post)
    db.commit()
    return {"detail": "Post deleted"}

# User creation
@app.post("/users/", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserBase, db: db_dependency):
    # Hash the plain-text password using bcrypt
    hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt())
    
    # Create a new user object with the hashed password
    db_user = models.User(
        username=user.username,
        password=hashed_password.decode('utf-8')  # Store the hashed password
    )
    
    db.add(db_user)
    db.commit()

# Read user by ID
@app.get("/users/{user_id}", status_code=status.HTTP_200_OK)
async def read_user(user_id: int, db: db_dependency):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# Add this at the end of your file
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)