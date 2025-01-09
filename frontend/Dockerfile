FROM oven/bun:latest

# Set working directory
WORKDIR /app

# First, copy only package.json and bun.lockb
# This helps with layer caching - if dependencies haven't changed,
# we can reuse the cached layer from previous builds
COPY package.json bun.lockb ./

# Install dependencies using bun
RUN bun install

# Copy all other source files
# We do this after installing dependencies so that changes to source code
# don't invalidate our dependency cache
COPY . .

# Build the application
# This creates a production build in the /app/dist directory
RUN bun run build

# Set up a command to serve the built files
# Using vite preview to serve the production build
CMD ["bunx", "--bun", "vite", "preview", "--host", "0.0.0.0", "--port", "5173"]
