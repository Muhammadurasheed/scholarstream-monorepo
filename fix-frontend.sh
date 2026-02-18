#!/bin/bash
echo "🔧 Fixing Frontend Native Binding Issue..."
echo ""
echo "Step 1: Cleaning old dependencies..."
rm -rf node_modules package-lock.json
echo "✅ Cleaned"
echo ""
echo "Step 2: Reinstalling with force flag..."
npm install --force
echo ""
echo "Step 3: Starting development server..."
npm run dev
