import React, { useState, useRef, useEffect } from 'react';
import Controls from './Controls';
import Content from './Content';
import Header from './Header';

function App() {
  const [presents, setPresents] = useState('');
  const [loading, setLoading] = useState(false);
  const abortControllerRef = useRef(null);

  const [teamMembers, setTeamMembers] = useState([]);

  useEffect(() => {
    const fetchTeamMembers = async () => {
      try {
        const response = await fetch('/api/teamMembers');
        if (!response.ok) {
          throw new Error(`Error: ${response.status}`);
        }
        const data = await response.json();
        setTeamMembers(data.teamMembers);
      } catch (error) {
        console.error('Failed to fetch teamMembers:', error);
      }
    };

    fetchTeamMembers();
  }, []);

  // Cleanup function for in-progress requests
  useEffect(() => {
    return () => {
      // Abort any in-progress fetch when component unmounts
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const fetchPresents = async (teamMember) => {
    setLoading(true);
    setPresents('');

    // Abort any previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create an AbortController to handle cleanup
    const controller = new AbortController();
    const signal = controller.signal;
    abortControllerRef.current = controller;

    try {
      const response = await fetch(
        `/api/trending/${encodeURIComponent(teamMember)}`,
        {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            Accept: 'text/event-stream',
          },
          signal, // Add the abort signal
        }
      );

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let done, value;

      while (!done) {
        ({ value, done } = await reader.read());
        if (signal.aborted || done) break;

        const text = decoder.decode(value, { stream: true });
        setPresents((prev) => prev + text);
      }
    } catch (error) {
      console.error('Error fetching presents:', error);
      setPresents('Error fetching presents. Please try again.');
    } finally {
      if (!signal.aborted) {
        setLoading(false);
        // Clear the abortControllerRef if this request is complete and not aborted
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
      }
    }
  };

  return (
    <div className="container">
      <Header />
      {teamMembers.length > 0 && (
        <div className="main-content">
          <div className="controls-wrapper">
            <Controls
              teamMembers={teamMembers}
              onSubmit={fetchPresents}
              loading={loading}
            />
          </div>
          <div className="content-wrapper">
            <Content presents={presents} loading={loading} />
          </div>
        </div>
      )}
      <style jsx>{`
        .container {
          height: 100vh;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }
        .main-content {
          display: flex;
          flex: 1;
          gap: 24px;
          padding: 24px;
          min-height: 0; /* This is crucial for nested flex containers to scroll */
          overflow: hidden; /* Prevent content from spilling out */
        }
        .controls-wrapper {
          width: 40%;
          min-width: 300px;
          overflow-y: auto; /* Make controls scrollable */
        }
        .content-wrapper {
          flex: 1;
          overflow-y: auto; /* Make content scrollable */
        }
      `}</style>
    </div>
  );
}

export default App;
