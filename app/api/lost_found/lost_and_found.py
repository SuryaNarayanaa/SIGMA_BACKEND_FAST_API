import uuid

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel
from pytz import timezone

from fastapi.responses import  JSONResponse
from fastapi import Depends
from fastapi import Form, UploadFile, File

from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorGridFSBucket

from app.api.lost_found import lost_and_found_router
from app.database.session import get_db
import base64
from bson import ObjectId

class RemoveLostItemRequest(BaseModel):
    item_id: str
    

@lost_and_found_router.post("/raise_lost_item", response_class=JSONResponse)
async def raise_lost_item(
    name: str = Form(...),
    roll_no: str = Form(...),
    contact_number: str = Form(...),
    email: str = Form(...),
    department: str = Form(...),
    item_name: str = Form(...),
    category: str = Form(...),
    description: str = Form(...),
    date_lost: Optional[str] = Form(None),
    last_seen_location: str = Form(...),
    comments: Optional[str] = Form(""),
    user_account_id: str = Form(...),
    images: List[UploadFile] = File([]),
    db: AsyncIOMotorDatabase = Depends(get_db)
    ):


    try:
        # Generate a unique item_id
        unique_item_id = str(uuid.uuid4())

        # Use current date if not provided
        if date_lost is None:
            date_lost = datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d")
        fs = AsyncIOMotorGridFSBucket(db)

        # Store the images in GridFS (if provided)
        image_ids = []
        for image in images:
            if image.filename:
                # Save the image file to GridFS
                content = await image.read()
                image_id = await fs.upload_from_stream(
                    filename=image.filename,
                    source=content,
                    metadata={"content_type": image.content_type}
                )
                image_ids.append(str(image_id))
        # Build the lost item document
        lost_item = {
            "item_id": unique_item_id,
            "name": name,
            "roll_no": roll_no,
            "contact_number": contact_number,
            "email": email,
            "department": department,
            "item_details": {
                "item_name": item_name,
                "category": category,
                "description": description,
            },
            "date_lost": date_lost,
            "last_seen_location": last_seen_location,
            "comments": comments,
            "reported_on": datetime.now(timezone("Asia/Kolkata")).strftime("%Y-%m-%d %H:%M:%S"),
            "image_ids": image_ids,
            "user_account_id": user_account_id
        }

        # Insert the document into MongoDB
        result = await db.lostandfound.insert_one(lost_item)
        if result.acknowledged:

            return JSONResponse(
                content={
                    "message": "Lost item reported successfully!",
                    "item_id": unique_item_id,
                    "image_ids": image_ids if image_ids else "No images uploaded"
                },
                status_code=201
            )
        
        return JSONResponse(
            content={
                "error": "Failed to insert lost item into the database.",
                "message": "Failed to report lost item"
            },
            status_code=500
            )

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "message": "Failed to report lost item"
            },
            status_code=400
        )

@lost_and_found_router.get("/get_all_lost_items", response_class=JSONResponse)
async def get_all_lost_items( db: AsyncIOMotorDatabase = Depends(get_db) ):

    try:
        # Initialize GridFS
        fs = AsyncIOMotorGridFSBucket(db)

        # Query all documents from the 'lostandfound' collection
        lost_items_cursor = db.lostandfound.find({})
        lost_items = []

        async for item in lost_items_cursor:
            # Convert BSON ObjectId to string for JSON compatibility
            item["_id"] = str(item["_id"])
            
            # Retrieve images if 'image_ids' exists
            if "image_ids" in item:
                item["images"] = []  # Initialize list for images
                
                for image_id in item["image_ids"]:
                    try:
                        # Fetch the image file from GridFS
                        grid_out = await fs.open_download_stream(ObjectId(image_id))
                        image_data = await grid_out.read()
                        
                        # Encode the image content to Base64
                        image_base64 = base64.b64encode(image_data).decode("utf-8")
                        content_type = grid_out.metadata.get('content_type', 'image/png') if grid_out.metadata else 'image/png'
                        item["images"].append(f"data:{content_type};base64,{image_base64}")
                    except Exception as e:
                        print(f"Error fetching image: {e}")
                        item["images"].append(None)
            
            lost_items.append(item)

        # Return the data as JSON
        return JSONResponse(content={"lost_items": lost_items}, status_code=200)

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "message": "Failed to retrieve lost items"
            },
            status_code=500
        )




@lost_and_found_router.post("/remove_lost_item", response_class=JSONResponse)
async def remove_lost_item(input_data: RemoveLostItemRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    item_id = input_data.item_id
    fs = AsyncIOMotorGridFSBucket(db)
    try:
        # Find the lost item in the database
        lost_item = await db.lostandfound.find_one({"item_id": item_id})

        if lost_item:
            # Delete associated images from GridFS
            if "image_ids" in lost_item and isinstance(lost_item["image_ids"], list):
                # Use a list comprehension to create a list of ObjectIds, handling potential conversion errors
                object_ids_to_delete = []
                for image_id in lost_item["image_ids"]:
                    try:
                        object_ids_to_delete.append(ObjectId(image_id))
                    except Exception as e:
                        print(f"Invalid image_id {image_id}: {e}")

                # Delete images from GridFS in a single operation
                if object_ids_to_delete:
                    try:
                        await fs.delete_many(object_ids_to_delete)
                    except Exception as e:
                        print(f"Failed to delete images: {e}")

            # Remove the lost item document from MongoDB
            result = await db.lostandfound.delete_one({"item_id": item_id})

            if result.deleted_count > 0:
                return JSONResponse(
                    content={
                        "message": "Lost item removed successfully!",
                        "item_id": item_id
                    },
                    status_code=200
                )
            else:
                return JSONResponse(
                    content={
                        "error": "Failed to remove lost item from the database.",
                        "message": "Failed to remove lost item"
                    },
                    status_code=500
                )
        else:
            return JSONResponse(
                content={
                    "error": "Lost item not found.",
                    "message": "Failed to remove lost item"
                },
                status_code=404
            )

    except Exception as e:
        return JSONResponse(
            content={
                "error": str(e),
                "message": "Failed to remove lost item"
            },
            status_code=400
        )




