import React, { useState } from 'react';

function Controls({ teamMembers, onSubmit, loading }) {
  const [selectedTeamMember, setSelectedTeamMember] = useState('');

  const handleTeamMemberChange = (e) => {
    setSelectedTeamMember(e.target.value);
  };

  const handleSubmit = () => {
    if (selectedTeamMember) {
      onSubmit(selectedTeamMember);
    }
  };

  return (
    <div className="controls">
      <div className="control-row">
        <select
          value={selectedTeamMember}
          onChange={handleTeamMemberChange}
          disabled={loading}
          className="category-select"
        >
          <option value="" disabled>
            Select team member
          </option>
          {teamMembers.map((teamMember) => (
            <option key={teamMember} value={teamMember}>
              {teamMember}
            </option>
          ))}
        </select>
        <button
          onClick={handleSubmit}
          disabled={!selectedTeamMember || loading}
          className="submit-button"
        >
          {loading ? (
            <>
              <span className="loading"></span>
              Processing...
            </>
          ) : (
            'Show me trending information'
          )}
        </button>
      </div>
    </div>
  );
}

export default Controls;
