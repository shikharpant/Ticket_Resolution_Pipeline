# GST Grievance Resolution System - Frontend

A modern, professional React frontend for the GST Grievance Resolution Multi-Agent System, built with TypeScript, Tailwind CSS, and Vite.

## 🎯 Overview

This frontend provides a sophisticated user interface for interacting with the AI-powered GST grievance resolution system. It features real-time agent progress tracking, comprehensive query submission, and beautiful result visualization.

## ✨ Features

- **🎨 Modern UI/UX Design**: Clean, professional interface inspired by Claude/OpenAI with glass morphism effects
- **⚡ Real-time Processing**: Live agent status updates with smooth animations
- **📱 Responsive Design**: Works seamlessly on desktop, tablet, and mobile devices
- **🔍 Query Management**: Submit GST queries with categorization and track processing history
- **📊 Results Visualization**: Comprehensive display of resolution results with confidence scores and source attribution
- **💾 Session History**: Persistent query history with search and filtering capabilities
- **🎭 Smooth Animations**: Beautiful transitions and micro-interactions using Framer Motion

## 🛠 Technology Stack

- **React 18** - Modern React with hooks and concurrent features
- **TypeScript** - Type-safe development experience
- **Vite** - Fast build tool and development server
- **Tailwind CSS** - Utility-first CSS framework with custom design system
- **Framer Motion** - Declarative animations and gestures
- **React Markdown** - Rich text rendering for results
- **Lucide React** - Beautiful icon library

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Base UI components (Button, Card, Input, etc.)
│   │   ├── AgentStatusDisplay.tsx
│   │   ├── QueryForm.tsx
│   │   ├── QueryHistory.tsx
│   │   └── ResultsDisplay.tsx
│   ├── hooks/              # Custom React hooks
│   │   └── useAgentProgress.ts
│   ├── lib/                # Utilities and configurations
│   │   ├── api.ts          # API client and configuration
│   │   └── utils.ts        # Utility functions
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts
│   ├── pages/              # Main application pages
│   │   └── HomePage.tsx
│   ├── App.tsx             # Root application component
│   ├── main.tsx            # Application entry point
│   └── index.css           # Global styles and Tailwind imports
├── public/                 # Static assets
├── index.html              # HTML template
├── package.json            # Dependencies and scripts
├── tailwind.config.js      # Tailwind CSS configuration
├── tsconfig.json           # TypeScript configuration
└── vite.config.ts          # Vite build configuration
```

## 🚀 Getting Started

### Prerequisites

- Node.js 16+ and npm
- The backend server running on `http://localhost:8000`

### Installation

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm run dev
   ```

3. **Open your browser**:
   Navigate to `http://localhost:3000`

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run type-check` - Run TypeScript type checking
- `npm run lint` - Run ESLint for code quality

## 🎨 Design System

### Color Palette

- **Primary Blue**: #3b82f6 (for primary actions and highlights)
- **Accent Teal**: #14b8a6 (for secondary elements and gradients)
- **Success Green**: #22c55e (for success states and completed actions)
- **Warning Amber**: #f59e0b (for warnings and pending states)
- **Error Red**: #ef4444 (for errors and failed states)
- **Neutral Grays**: #fafafa to #171717 (for text and backgrounds)

### Typography

- **Font Family**: Inter (system fonts as fallback)
- **Weights**: 300 (Light), 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold)
- **Responsive**: Fluid typography that scales with viewport size

### UI Components

All UI components follow the **Atomic Design** pattern:

1. **Atoms**: Basic elements (Button, Input, Icon)
2. **Molecules**: Component compositions (QueryForm, AgentStatus)
3. **Organisms**: Complex structures (HomePage, ResultsDisplay)
4. **Templates**: Layout patterns
5. **Pages**: Complete application views

## 🔄 API Integration

The frontend communicates with the backend via REST API and WebSocket connections:

### REST Endpoints

- `GET /api/status` - System status and health check
- `POST /api/query` - Submit new GST query
- `GET /api/query/{id}/result` - Retrieve query results
- `GET /api/history` - Get query history
- `DELETE /api/history` - Clear query history

### WebSocket Connection

- `WS /ws/{session_id}` - Real-time agent progress updates

### API Client Configuration

The API client is configured in `src/lib/api.ts` with:
- Automatic error handling
- Request/response interceptors
- WebSocket connection management
- Type-safe interfaces

## 🎯 Key Features

### Real-time Agent Progress

The system provides live updates as each agent processes the query:

1. **Preprocessing Agent** - Query cleaning and entity extraction
2. **Classification Agent** - Intent and category classification
3. **Multi-Source Retrieval** - Knowledge base and web search
4. **Resolution Agent** - Issue analysis and solution generation
5. **Response Generation** - Final response formatting

### Query Submission

Users can submit GST queries with:
- **Category Selection**: 15+ GST categories (Registration, Returns, Payments, etc.)
- **Rich Text Input**: Detailed query description with formatting
- **Validation**: Client-side validation with helpful error messages

### Results Display

Comprehensive result visualization including:
- **Confidence Scores**: Visual indicators with percentage values
- **Source Attribution**: Breakdown of information sources used
- **Detailed Analysis**: Full resolution with markdown formatting
- **Processing Metrics**: Time taken and sources consulted

### Session Management

- **Query History**: Persistent storage of all submitted queries
- **Search & Filter**: Find specific queries quickly
- **Status Tracking**: Processing, completed, error states
- **Export Options**: Copy results to clipboard

## 📱 Responsive Design

The interface is fully responsive with:

- **Mobile-first approach**: Optimized for mobile devices
- **Breakpoints**: sm (640px), md (768px), lg (1024px), xl (1280px)
- **Adaptive layouts**: Different layouts for different screen sizes
- **Touch-friendly**: Large tap targets and touch gestures

## 🎭 Animations

Smooth, meaningful animations enhance the user experience:

- **Page Transitions**: Fade and slide animations between states
- **Loading States**: Skeleton screens and progress indicators
- **Micro-interactions**: Hover effects and button feedback
- **Agent Progress**: Animated status updates with smooth transitions

## 🔧 Configuration

### Environment Variables

Create a `.env.local` file for local configuration:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_TITLE="GST Grievance Resolution System"
```

### Build Configuration

- **Vite**: Fast development and optimized production builds
- **TypeScript**: Strict type checking with path mapping
- **Tailwind**: JIT compilation with custom design tokens
- **Asset Optimization**: Automatic image optimization and bundling

## 🚀 Deployment

### Production Build

```bash
npm run build
```

The build output will be in the `dist/` directory, ready for deployment to any static hosting service.

### Deployment Options

- **Vercel**: Zero-config deployment with automatic HTTPS
- **Netlify**: Continuous deployment from Git repository
- **AWS S3 + CloudFront**: Scalable static hosting
- **Docker**: Containerized deployment with Nginx

## 🔍 Development Tips

### Code Style

- **TypeScript**: Strict mode with comprehensive type definitions
- **ESLint**: Airbnb style guide with React rules
- **Prettier**: Consistent code formatting
- **Husky**: Pre-commit hooks for code quality

### Performance

- **Code Splitting**: Automatic route-based code splitting
- **Tree Shaking**: Unused code elimination
- **Image Optimization**: Lazy loading and WebP support
- **Bundle Analysis**: Built-in bundle analyzer

### Debugging

- **React DevTools**: Component inspection and debugging
- **Redux DevTools**: State management debugging (if using Redux)
- **Network Tab**: API request/response monitoring
- **Console**: Structured logging with different levels

## 🤝 Contributing

1. Follow the established code style and patterns
2. Add TypeScript types for new components and functions
3. Include proper error handling and loading states
4. Test on different screen sizes and browsers
5. Document new features and API changes

## 📄 License

This project is part of the GST Grievance Resolution System. See the main project license for details.

## 🆘 Support

For issues and questions:

1. Check the [console](./console) for backend issues
2. Review the [main README](../README.md) for system-wide information
3. Create an issue with detailed description and steps to reproduce

---

Built with ❤️ using modern web technologies for efficient and delightful user experiences.