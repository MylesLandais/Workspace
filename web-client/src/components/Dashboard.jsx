import React, { useState } from 'react';
import DashboardGrid from './DashboardGrid.jsx';
import RedditFeedWidget from './RedditFeedWidget.jsx';

const WidgetLayout = [
    { id: 'reddit-feed', x: 0, y: 0, w: 4, h: 8, type: 'reddit' },
    { id: 'inbox', x: 4, y: 0, w: 4, h: 4, type: 'inbox' },
    { id: 'readwise', x: 8, y: 0, w: 4, h: 4, type: 'readwise' },
    { id: 'chart', x: 4, y: 4, w: 8, h: 4, type: 'chart' },
];

const Dashboard = () => {
    // NOTE: In a real app, this state would be initialized from localStorage or a backend API
    const [layout, setLayout] = useState(WidgetLayout);

    // Maps the layout data to the actual React components
    const renderWidget = (widget) => {
        switch (widget.type) {
            case 'reddit':
                return <RedditFeedWidget />;
            case 'inbox':
                return (
                    <>
                        <h3 className="text-xl font-bold text-teal-400 border-b border-gray-700 pb-2">Inbox (WIP)</h3>
                        <p className="text-gray-500 mt-2">New messages: 3</p>
                        <p className="text-gray-600">The inbox widget will show new content from various sources, prioritized by importance.</p>
                    </>
                );
            case 'readwise':
                return (
                    <>
                        <h3 className="text-xl font-bold text-teal-400 border-b border-gray-700 pb-2">Readwise Highlights (Mock)</h3>
                        <p className="text-gray-500 mt-2">Quote of the day:</p>
                        <blockquote className="border-l-4 border-emerald-500 pl-3 italic text-gray-300">"The only true wisdom is in knowing you know nothing." - Socrates</blockquote>
                    </>
                );
            case 'chart':
                return (
                    <>
                        <h3 className="text-xl font-bold text-teal-400 border-b border-gray-700 pb-2">Post Velocity Chart (Mock)</h3>
                        <div className="h-48 flex items-center justify-center text-gray-500">
                            [Placeholder for Chart Library Integration]
                        </div>
                    </>
                );
            default:
                return <h3 className="text-red-400">Unknown Widget Type</h3>;
        }
    };

    const handleLayoutChange = (newLayout) => {
        // Persist the layout in a real app
        setLayout(newLayout);
    };

    return (
        <div className="p-4 sm:p-0">
            <DashboardGrid 
                layout={layout} 
                renderWidget={renderWidget} 
                onLayoutChange={handleLayoutChange} 
            />
        </div>
    );
};

export default Dashboard;
