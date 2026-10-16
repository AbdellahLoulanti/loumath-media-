# LouMath media

Daily Instagram content for [@loumath2025](https://www.instagram.com/loumath2025/): maths and physics tutoring at home in Tétouan, M'diq and Martil.

- `media/YYYY-MM-DD/`: the two posts (`post1.jpg`, `post2.jpg`) and the reel (`reel.mp4`) for each day.
- `schedule.json`: what to publish each day, with captions.
- `publish.py`: publishes the day's items through the Instagram API (needs `IG_TOKEN`). A scheduled cloud task runs it every day at 13:00, Morocco time.

Test without publishing: `python publish.py 2026-10-17 --dry-run`
