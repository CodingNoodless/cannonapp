import asyncio
import os
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DATABASE", "cannon_db")

async def seed_courses():
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]
    
    print(f"Connecting to {MONGODB_URI}, DB: {DB_NAME}")
    
    # Clear existing courses
    await db.courses.delete_many({})
    print("Cleared existing courses.")

    courses = [
        # --- VIDEO COURSES (5) ---
        {
            "title": "Mewing Masterclass",
            "description": "Master the art of proper tongue posture to reshape your jawline and improve facial structure.",
            "category": "mewing",
            "thumbnail_url": "https://images.unsplash.com/photo-1597223506889-498ccf1e03a4?w=500",
            "difficulty": "beginner",
            "estimated_weeks": 4,
            "modules": [
                {
                    "module_number": 1,
                    "title": "The Basics",
                    "description": "Essential techniques for beginners.",
                    "chapters": [
                        {
                            "chapter_id": "mew_v1_c1",
                            "title": "The Ultimate Mewing Guide",
                            "description": "Dr. Mike Mew explains the fundamentals.",
                            "type": "video",
                            "video_url": "https://www.youtube.com/watch?v=Ty-M7u8-w2k",
                            "duration_minutes": 15
                        },
                        {
                            "chapter_id": "mew_v1_c2",
                            "title": "Finding the 'N' Spot",
                            "description": "How to place your tongue tip correctly.",
                            "type": "video",
                            "video_url": "https://www.youtube.com/watch?v=UqQ2tNlK0t0",
                            "duration_minutes": 10
                        }
                    ]
                }
            ]
        },
        {
            "title": "Postural Correction",
            "description": "Fix forward head posture and rounded shoulders for a more masculine, dominant presence.",
            "category": "posture",
            "thumbnail_url": "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=500",
            "difficulty": "intermediate",
            "estimated_weeks": 6,
            "modules": [
                {
                    "module_number": 1,
                    "title": "Follow Along Routine",
                    "description": "Daily exercises for thoracic mobility.",
                    "chapters": [
                        {
                            "chapter_id": "pos_v1_c1",
                            "title": "10 Minute Posture Fix",
                            "description": "Follow this routine daily to see results.",
                            "type": "video",
                            "video_url": "https://www.youtube.com/watch?v=y_ltZI-gSbs",
                            "duration_minutes": 10
                        },
                        {
                            "chapter_id": "pos_v1_c2",
                            "title": "3 Exercises for Instant Change",
                            "description": "Quick fixes for common posture issues.",
                            "type": "video",
                            "video_url": "https://www.youtube.com/watch?v=Yn77u8F2U2Y",
                            "duration_minutes": 5
                        }
                    ]
                }
            ]
        },
        {
            "title": "Advanced Mewing 2.0",
            "description": "Take your progress further with hard mewing and swallowing techniques.",
            "category": "mewing",
            "thumbnail_url": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=500",
            "difficulty": "advanced",
            "estimated_weeks": 8,
            "modules": [
                {
                    "module_number": 1,
                    "title": "Pressure & Consistency",
                    "description": "How to maintain posture even while sleeping.",
                    "chapters": [
                        {
                            "chapter_id": "mew_v2_c1",
                            "title": "Mewing 2.0 Techniques",
                            "description": "Advanced tongue pressure methods.",
                            "type": "video",
                            "video_url": "https://www.youtube.com/watch?v=d_k8k8U_d_c",
                            "duration_minutes": 12
                        }
                    ]
                }
            ]
        },
        {
            "title": "Professional Skincare Guide",
            "description": "Build a solid routine to clear acne and achieve radiant, healthy-looking skin.",
            "category": "skincare",
            "thumbnail_url": "https://images.unsplash.com/photo-1556227702-d1e4e7b5c232?w=500",
            "difficulty": "beginner",
            "estimated_weeks": 3,
            "modules": [
                {
                    "module_number": 1,
                    "title": "The Routine",
                    "description": "Cleansing, moisturizing, and protection.",
                    "chapters": [
                        {
                            "chapter_id": "skin_v1_c1",
                            "title": "Dermatologist's Morning Routine",
                            "description": "Start your day with the right products.",
                            "type": "video",
                            "video_url": "https://www.youtube.com/watch?v=wN3He6mQ-l0",
                            "duration_minutes": 8
                        }
                    ]
                }
            ]
        },
        {
            "title": "Facial Yoga & Definition",
            "description": "Manual exercises to tone your facial muscles and reduce puffiness.",
            "category": "jawline",
            "thumbnail_url": "https://images.unsplash.com/photo-1616391182219-e080b4d1043a?w=500",
            "difficulty": "intermediate",
            "estimated_weeks": 4,
            "modules": [
                {
                    "module_number": 1,
                    "title": "Muscle Toning",
                    "description": "Targeting the masseters and cheekbones.",
                    "chapters": [
                        {
                            "chapter_id": "face_v1_c1",
                            "title": "Face Exercises for Jawline",
                            "description": "Simple movements to sharpen your lower face.",
                            "type": "video",
                            "video_url": "https://www.youtube.com/watch?v=1pE6F4vnyo8",
                            "duration_minutes": 12
                        }
                    ]
                }
            ]
        },

        # --- PHOTO COURSES (5) ---
        {
            "title": "Eyebrow Grooming Styles",
            "description": "Learn which eyebrow shape best fits your face to look more masculine and alert.",
            "category": "hair",
            "thumbnail_url": "https://images.unsplash.com/photo-1583243542446-2f08581696aa?w=500",
            "difficulty": "beginner",
            "estimated_weeks": 2,
            "modules": [
                {
                    "module_number": 1,
                    "title": "The Golden Ratio",
                    "description": "Visualizing the perfect proportions.",
                    "chapters": [
                        {
                            "chapter_id": "brow_p1_c1",
                            "title": "Ideal Shape Examples",
                            "description": "High-quality visual guide to eyebrow arches.",
                            "type": "image",
                            "image_url": "https://images.unsplash.com/photo-1583243542446-2f08581696aa",
                            "duration_minutes": 5
                        }
                    ]
                }
            ]
        },
        {
            "title": "Face Shape Identification",
            "description": "Discover if you have an oval, square, or heart-shaped face through visual analysis.",
            "category": "jawline",
            "thumbnail_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=500",
            "difficulty": "beginner",
            "estimated_weeks": 1,
            "modules": [
                {
                    "module_number": 1,
                    "title": "The 6 Face Shapes",
                    "description": "Detailed photos of each facial structure.",
                    "chapters": [
                        {
                            "chapter_id": "face_p1_c1",
                            "title": "The Square Jaw",
                            "description": "Characteristics of the most masculine face shape.",
                            "type": "image",
                            "image_url": "https://images.unsplash.com/photo-1506793081023-ec66d953f65e",
                            "duration_minutes": 3
                        }
                    ]
                }
            ]
        },
        {
            "title": "Skin Texture Analysis",
            "description": "A visual guide to identifying skin issues from acne to scarring.",
            "category": "skincare",
            "thumbnail_url": "https://images.unsplash.com/photo-1522335789203-aabd1fc54bc9?w=500",
            "difficulty": "intermediate",
            "estimated_weeks": 2,
            "modules": [
                {
                    "module_number": 1,
                    "title": "Macro Analysis",
                    "description": "Close-up shots of different skin conditions.",
                    "chapters": [
                        {
                            "chapter_id": "skin_p1_c1",
                            "title": "Glossy Skin vs Oily Skin",
                            "description": "Understanding the visual difference.",
                            "type": "image",
                            "image_url": "https://images.unsplash.com/photo-1616394158624-a2ba99279bd0",
                            "duration_minutes": 5
                        }
                    ]
                }
            ]
        },
        {
            "title": "Fashion for Your Frame",
            "description": "Visual examples of how clothing affects your perceived jawline and shoulder width.",
            "category": "mindset",
            "thumbnail_url": "https://images.unsplash.com/photo-1490114538077-0a7f8cb49891?w=500",
            "difficulty": "beginner",
            "estimated_weeks": 4,
            "modules": [
                {
                    "module_number": 1,
                    "title": "V-Taper Aesthetics",
                    "description": "How jacket cuts change your silhouette.",
                    "chapters": [
                        {
                            "chapter_id": "fash_p1_c1",
                            "title": "The Power of the Lapel",
                            "description": "Widening your shoulders through smart styling.",
                            "type": "image",
                            "image_url": "https://images.unsplash.com/photo-1507679799987-c7377ec48696",
                            "duration_minutes": 7
                        }
                    ]
                }
            ]
        },
        {
            "title": "Grooming Master Tools",
            "description": "A visual encyclopedia of the best tools for looksmaxxing.",
            "category": "hair",
            "thumbnail_url": "https://images.unsplash.com/photo-1599351431247-f10bc064971c?w=500",
            "difficulty": "intermediate",
            "estimated_weeks": 2,
            "modules": [
                {
                    "module_number": 1,
                    "title": "Precision Cutting",
                    "description": "Comparing different guard sizes and trimmers.",
                    "chapters": [
                        {
                            "chapter_id": "tool_p1_c1",
                            "title": "The Detailer",
                            "description": "Getting those sharp edges.",
                            "type": "image",
                            "image_url": "https://images.unsplash.com/photo-1599351431247-f10bc064971c",
                            "duration_minutes": 4
                        }
                    ]
                }
            ]
        },

        # --- TEXT COURSES (5) ---
        {
            "title": "Mindset of the Elite",
            "description": "Develop the psychological foundation needed to sustain a long-term transformation.",
            "category": "mindset",
            "thumbnail_url": "https://images.unsplash.com/photo-1494145904049-0dca59b4bbad?w=500",
            "difficulty": "beginner",
            "estimated_weeks": 4,
            "modules": [
                {
                    "module_number": 1,
                    "title": "Discipline is Freedom",
                    "description": "Building unshakeable habits.",
                    "chapters": [
                        {
                            "chapter_id": "mind_t1_c1",
                            "title": "The 1% Rule",
                            "description": "Small daily improvements compound over time. Focus on the process over the result.",
                            "type": "text",
                            "content": "To become part of the top 1%, you must do what the other 99% aren't willing to do. This course covers the stoic philosophy of self-improvement.",
                            "duration_minutes": 15
                        }
                    ]
                }
            ]
        },
        {
            "title": "Nutrition for Face Fat Loss",
            "description": "Which foods cause water retention and how to achieve a lean, hollow-cheek look.",
            "category": "fat_loss",
            "thumbnail_url": "https://images.unsplash.com/photo-1547514701-42782101795e?w=500",
            "difficulty": "intermediate",
            "estimated_weeks": 5,
            "modules": [
                {
                    "module_number": 1,
                    "title": "Inflammation & Sodium",
                    "description": "The science of facial puffiness.",
                    "chapters": [
                        {
                            "chapter_id": "nut_t1_c1",
                            "title": "The Seed Oil Truth",
                            "description": "Why avoiding processed oils changes your skin and fat storage.",
                            "type": "text",
                            "content": "Linoleic acid in seed oils can lead to chronic inflammation. Stick to animal fats and coconut oil for better hormonal health.",
                            "duration_minutes": 20
                        }
                    ]
                }
            ]
        },
        {
            "title": "Sleep Optimization for Looks",
            "description": "How quality rest impacts collagen production and facial growth hormones.",
            "category": "skincare",
            "thumbnail_url": "https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=500",
            "difficulty": "beginner",
            "estimated_weeks": 2,
            "modules": [
                {
                    "module_number": 1,
                    "title": "The Deep Sleep Phase",
                    "description": "Maximizing HGH production at night.",
                    "chapters": [
                        {
                            "chapter_id": "sleep_t1_c1",
                            "title": "Temperature & Darkness",
                            "description": "Setting up the perfect environment for beauty sleep.",
                            "type": "text",
                            "content": "Maintain a room temperature of 65°F (18°C) and ensure total darkness to maximize melatonin. This repair phase is when your skin regenerates.",
                            "duration_minutes": 15
                        }
                    ]
                }
            ]
        },
        {
            "title": "Hormonal Optimization Guide",
            "description": "The role of testosterone in bone density and facial development.",
            "category": "mindset",
            "thumbnail_url": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=500",
            "difficulty": "advanced",
            "estimated_weeks": 6,
            "modules": [
                {
                    "module_number": 1,
                    "title": "The T-Level Baseline",
                    "description": "Natural ways to boost androgens.",
                    "chapters": [
                        {
                            "chapter_id": "horm_t1_c1",
                            "title": "Zinc & Vitamin D",
                            "description": "The essential minerals for a masculine facial structure.",
                            "type": "text",
                            "content": "Testosterone levels are directly linked to brow ridge development and jawline width. Optimize through sunlight and supplementation.",
                            "duration_minutes": 25
                        }
                    ]
                }
            ]
        },
        {
            "title": "The Science of Aesthetics",
            "description": "Understanding the mathematical principles of beauty: symmetry, ratios, and harmony.",
            "category": "mindset",
            "thumbnail_url": "https://images.unsplash.com/photo-1503023345037-916b411a4969?w=500",
            "difficulty": "intermediate",
            "estimated_weeks": 3,
            "modules": [
                {
                    "module_number": 1,
                    "title": "The Golden Ratio",
                    "description": "How 1.618 applies to the human face.",
                    "chapters": [
                        {
                            "chapter_id": "sci_t1_c1",
                            "title": "Facial Thirds",
                            "description": "How balance between the forehead, nose, and chin creates harmony.",
                            "type": "text",
                            "content": "Symmetry is a biological indicator of health. While nobody is perfectly symmetrical, small grooming hacks can emphasize your best ratios.",
                            "duration_minutes": 15
                        }
                    ]
                }
            ]
        }
    ]

    for course in courses:
        course["is_active"] = True
        course["created_at"] = datetime.utcnow()
        course["updated_at"] = datetime.utcnow()
        await db.courses.insert_one(course)
        print(f"Created course: {course['title']}")

    print("\nGenuine courses seeded successfully!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_courses())
