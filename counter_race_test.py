"""
An experiment to see if my proposed ID assignment mechanism would be susceptible to
race conditions.
"""

import asyncio

current_id = 0
all_ids = []

async def mock_new_connection() -> None:
    global all_ids, current_id

    my_id = current_id
    all_ids.append(current_id)
    current_id += 1

async def main() -> None:
    global all_ids, current_id

    print(f"start with {current_id=}")

    tasks = [asyncio.create_task(mock_new_connection()) for _ in range(10000)]
    await asyncio.gather(*tasks)

    print(f"end with {current_id=}")

    print(f"{all_ids[-3:]=}")

    print("checking for duplicates...")
    for i, x in enumerate(all_ids):
        if x in all_ids[i+1:]:
            print("duplicate id detected")

if __name__ == "__main__":
    asyncio.run(main())
