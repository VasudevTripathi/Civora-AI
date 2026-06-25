import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import CommandMenu from './components/CommandMenu';
import DashboardView from './components/DashboardView';
import WizardView from './components/WizardView';
import ChatView from './components/ChatView';
import CalendarView from './components/CalendarView';
import DocumentsView from './components/DocumentsView';
import './index.css';

export default function App() {
  const [activeView, setActiveView] = useState('dashboard');
  const [entityProgress, setEntityProgress] = useState(0); // 0% (unregistered) -> 100% (incorporated)
  const [isCommandOpen, setIsCommandOpen] = useState(false);

  // Listen for Cmd+K / Ctrl+K keyboard shortcut (Linear style)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsCommandOpen(prev => !prev);
      }
      if (e.key === 'Escape') {
        setIsCommandOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const renderActiveView = () => {
    switch (activeView) {
      case 'dashboard':
        return <DashboardView entityProgress={entityProgress} onViewChange={setActiveView} />;
      case 'wizard':
        return (
          <WizardView
            entityProgress={entityProgress}
            onProgressUpdate={setEntityProgress}
            onViewChange={setActiveView}
          />
        );
      case 'chat':
        return <ChatView />;
      case 'calendar':
        return <CalendarView />;
      case 'documents':
        return <DocumentsView entityProgress={entityProgress} />;
      default:
        return <DashboardView entityProgress={entityProgress} onViewChange={setActiveView} />;
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <Sidebar
        activeView={activeView}
        onViewChange={setActiveView}
        entityProgress={entityProgress}
      />

      {/* Main Panel */}
      <div className="main-content">
        <Header
          activeView={activeView}
          entityProgress={entityProgress}
          onSearchClick={() => setIsCommandOpen(true)}
        />
        
        {/* Render active workspace panel */}
        <main className="view-container">
          {renderActiveView()}
        </main>
      </div>

      {/* Alfred / Command Menu Modal Overlay */}
      <CommandMenu
        isOpen={isCommandOpen}
        onClose={() => setIsCommandOpen(false)}
        onViewChange={setActiveView}
      />
    </div>
  );
}
