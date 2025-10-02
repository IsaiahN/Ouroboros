#!/usr/bin/env python3
"""
Quick test script to verify the evolution system works correctly
"""
import asyncio
from start_game import start_single_game

async def main():
    # Test with only 10 actions to avoid timeout
    await start_single_game(max_actions=10)

if __name__ == "__main__":
    asyncio.run(main())