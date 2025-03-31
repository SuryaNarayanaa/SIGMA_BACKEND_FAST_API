from fastapi.responses import JSONResponse
from fastapi import Depends

from datetime import datetime, timedelta
from motor.motor_asyncio import  AsyncIOMotorDatabase

from app.database.session import get_db
from app.api.tasks import tasks_router



@tasks_router.get("/", response_class= JSONResponse, tags=["Tasks Overview"])
async def get_all_issues(db: AsyncIOMotorDatabase = Depends(get_db)):

    # Use projection to exclude _id field directly in the query
    issues = await db.dataset.find({}, {'_id': 0}).to_list(length=None)
    
    return JSONResponse(content={"issues": issues}, status_code=200)


@tasks_router.get("/count", response_class= JSONResponse, tags=["Tasks Overview"])
async def count_issues(db: AsyncIOMotorDatabase = Depends(get_db)):

    current_date = datetime.now()
    date_365_days_ago = current_date - timedelta(days=365)
    date_30_days_ago = current_date - timedelta(days=30)

    pipeline = [
    {
        "$match": {
            "date": {"$exists": True},
            "$expr": {
                "$and": [
                    {"$ne": ["$date", ""]},
                    {"$ne": ["$date", None]}
                ]
            }
        }
    },
    {
        "$addFields": {
            "dateObj": {
                "$dateFromString": {
                    "dateString": {
                        "$concat": [
                            {"$substr": ["$date", 0, 6]},   # e.g. "29/11/"
                            "20",
                            {"$substr": ["$date", 6, 2]}    # e.g. "24" becomes "2024"
                        ]
                    },
                    "format": "%d/%m/%Y"
                }
            }
        }
    },
    {
        "$facet": {
            "last_365_days": [
                {
                    "$match": {
                        "dateObj": {"$gte": date_365_days_ago}
                    }
                },
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ],
            "last_30_days": [
                {
                    "$match": {
                        "dateObj": {"$gte": date_30_days_ago}
                    }
                },
                {
                    "$group": {
                        "_id": "$status",
                        "count": {"$sum": 1}
                    }
                }
            ]
        }
    }
]

    result = await db.dataset.aggregate(pipeline).to_list(length=None)
    
    # Process aggregation results to build stats dictionaries
    stats_365 = {doc["_id"]: doc["count"] for doc in result[0]["last_365_days"]}
    stats_30 = {doc["_id"]: doc["count"] for doc in result[0]["last_30_days"]}
    
    # Construct the response
    response_content = {
        "issues_last_365_days": {
            "total": stats_365.get("OPEN", 0) + stats_365.get("CLOSE", 0),
            "open": stats_365.get("OPEN", 0),
            "closed": stats_365.get("CLOSE", 0)
        },
        "issues_last_30_days": {
            "total": stats_30.get("OPEN", 0) + stats_30.get("CLOSE", 0),
            "open": stats_30.get("OPEN", 0),
            "closed": stats_30.get("CLOSE", 0)
        }
    }

    return JSONResponse(content=response_content, status_code=200)


@tasks_router.get("/todo", response_class= JSONResponse, tags=["Tasks Overview"])
async def task_list_table(db: AsyncIOMotorDatabase = Depends(get_db)):
    pipeline = [
        {
            "$match": {
                "status": "OPEN",
                "issue.issueType": "Complaint"
            }
        },
        {
            "$addFields": {
                "dateObj": {
                    "$dateFromString": {
                        "dateString": {
                            "$concat": [
                                {"$substr": ["$date", 0, 6]},  # e.g. "29/11/"
                                "20",
                                {"$substr": ["$date", 6, 2]}   # e.g. "24" becomes "2024"
                            ]
                        },
                        "format": "%d/%m/%Y"
                    }
                },
                "delay_days": {
                    "$dateDiff": {
                        "startDate": {
                            "$dateFromString": {
                                "dateString": {
                                    "$concat": [
                                        {"$substr": ["$date", 0, 6]},  # e.g. "29/11/"
                                        "20",
                                        {"$substr": ["$date", 6, 2]}   # e.g. "24" becomes "2024"
                                    ]
                                },
                                "format": "%d/%m/%Y"
                            }
                        },
                        "endDate": "$$NOW",
                        "unit": "day"
                    }
                }
            }
        },
        {
            "$set": {
                "priority": {
                    "$switch": {
                        "branches": [
                            {"case": {"$eq": ["$issue.issueType", "ISSUE"]}, "then": 1},
                            {"case": {"$eq": ["$issue.issueType", "SUGGESTION"]}, "then": 2}
                        ],
                        "default": 1
                    }
                }
            }
        },
        # Final projection: remove _id and dateObj from the output
        {
            "$project": {
                "_id": 0,
                "dateObj": 0
            }
        }
    ]
    
    issues = await db.dataset.aggregate(pipeline).to_list(length=None)
    return JSONResponse(content={"tasks": issues}, status_code=200)