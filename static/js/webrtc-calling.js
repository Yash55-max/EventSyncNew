/**
 * WebRTC Calling Interface for EVENTSYNC
 * Modern video/audio calling UI with comprehensive controls
 */

class WebRTCCallManager {
    constructor() {
        this.localStream = null;
        this.remoteStreams = new Map();
        this.peerConnections = new Map();
        this.socket = null;
        this.currentCallId = null;
        this.isInitiator = false;
        this.callType = 'video'; // 'video' or 'audio'
        this.participants = new Map();
        this.mediaSettings = {
            audio: true,
            video: true,
            screenShare: false
        };
        
        this.iceServers = [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' }
        ];
        
        this.initializeSocketConnection();
        this.setupEventListeners();
    }

    initializeSocketConnection() {
        if (typeof io !== 'undefined') {
            this.socket = io();
            this.setupSocketEventListeners();
        } else {
            console.error('Socket.IO not loaded');
        }
    }

    setupSocketEventListeners() {
        // Call management events
        this.socket.on('webrtc_call_joined', (data) => {
            console.log('Joined call:', data);
            this.handleCallJoined(data);
        });

        this.socket.on('webrtc_user_joined', (data) => {
            console.log('User joined:', data);
            this.handleUserJoined(data);
        });

        this.socket.on('webrtc_user_left', (data) => {
            console.log('User left:', data);
            this.handleUserLeft(data);
        });

        this.socket.on('webrtc_user_disconnected', (data) => {
            console.log('User disconnected:', data);
            this.handleUserLeft(data);
        });

        // WebRTC signaling events
        this.socket.on('webrtc_signal_received', (data) => {
            this.handleSignalingMessage(data);
        });

        this.socket.on('webrtc_ice_candidate_received', (data) => {
            this.handleIceCandidate(data);
        });

        // Media control events
        this.socket.on('webrtc_audio_toggled', (data) => {
            this.updateParticipantAudio(data.user_id, data.audio_enabled);
        });

        this.socket.on('webrtc_video_toggled', (data) => {
            this.updateParticipantVideo(data.user_id, data.video_enabled);
        });

        this.socket.on('webrtc_screen_share_toggled', (data) => {
            this.updateParticipantScreenShare(data.user_id, data.screen_share_enabled);
        });

        // Incoming call notifications
        this.socket.on('webrtc_incoming_call', (data) => {
            this.handleIncomingCall(data);
        });

        // Error handling
        this.socket.on('webrtc_error', (data) => {
            console.error('WebRTC Error:', data.error);
            this.showError(data.error);
        });
    }

    setupEventListeners() {
        // Call control buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('start-video-call')) {
                const targetUserId = e.target.dataset.userId;
                this.initiateCall('video', [targetUserId]);
            }
            
            if (e.target.classList.contains('start-audio-call')) {
                const targetUserId = e.target.dataset.userId;
                this.initiateCall('audio', [targetUserId]);
            }
            
            if (e.target.classList.contains('end-call-btn')) {
                this.endCall();
            }
            
            if (e.target.classList.contains('toggle-audio-btn')) {
                this.toggleAudio();
            }
            
            if (e.target.classList.contains('toggle-video-btn')) {
                this.toggleVideo();
            }
            
            if (e.target.classList.contains('toggle-screen-share-btn')) {
                this.toggleScreenShare();
            }
        });

        // Window/tab close event
        window.addEventListener('beforeunload', () => {
            if (this.currentCallId) {
                this.leaveCall();
            }
        });
    }

    async initiateCall(callType = 'video', targetUserIds = [], options = {}) {
        try {
            this.callType = callType;
            this.isInitiator = true;

            // Create call via API
            const response = await fetch('/api/webrtc/calls/initiate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    call_type: callType,
                    target_user_ids: targetUserIds,
                    ...options
                })
            });

            const result = await response.json();
            if (result.success) {
                this.currentCallId = result.call.call_id;
                await this.joinCall(this.currentCallId);
                this.showCallInterface(result.call);
            } else {
                throw new Error(result.error || 'Failed to initiate call');
            }
        } catch (error) {
            console.error('Error initiating call:', error);
            this.showError('Failed to start call: ' + error.message);
        }
    }

    async joinCall(callId) {
        try {
            this.currentCallId = callId;

            // Get user media
            await this.getUserMedia();

            // Join call via API
            const response = await fetch(`/api/webrtc/calls/${callId}/join`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    peer_id: this.generatePeerId()
                })
            });

            const result = await response.json();
            if (result.success) {
                // Join WebSocket room
                this.socket.emit('webrtc_join_call', {
                    call_id: callId,
                    session_id: this.generateSessionId()
                });

                this.showCallInterface(result.call);
                return result;
            } else {
                throw new Error(result.error || 'Failed to join call');
            }
        } catch (error) {
            console.error('Error joining call:', error);
            this.showError('Failed to join call: ' + error.message);
        }
    }

    async leaveCall() {
        try {
            if (!this.currentCallId) return;

            // Leave WebSocket room
            this.socket.emit('webrtc_leave_call', {
                call_id: this.currentCallId
            });

            // Leave call via API
            await fetch(`/api/webrtc/calls/${this.currentCallId}/leave`, {
                method: 'POST'
            });

            this.cleanup();
        } catch (error) {
            console.error('Error leaving call:', error);
        }
    }

    async endCall() {
        try {
            if (!this.currentCallId) return;

            // End call via API
            await fetch(`/api/webrtc/calls/${this.currentCallId}/end`, {
                method: 'POST'
            });

            this.cleanup();
        } catch (error) {
            console.error('Error ending call:', error);
        }
    }

    async getUserMedia() {
        try {
            const constraints = {
                audio: this.mediaSettings.audio,
                video: this.callType === 'video' ? this.mediaSettings.video : false
            };

            this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
            
            // Display local video
            const localVideo = document.getElementById('local-video');
            if (localVideo) {
                localVideo.srcObject = this.localStream;
                localVideo.muted = true; // Prevent echo
            }

            return this.localStream;
        } catch (error) {
            console.error('Error accessing media devices:', error);
            throw error;
        }
    }

    async toggleAudio() {
        if (!this.localStream) return;

        const audioTracks = this.localStream.getAudioTracks();
        const enabled = !this.mediaSettings.audio;
        
        audioTracks.forEach(track => {
            track.enabled = enabled;
        });

        this.mediaSettings.audio = enabled;

        // Update UI
        const button = document.querySelector('.toggle-audio-btn');
        if (button) {
            button.innerHTML = enabled ? 
                '<i class="fas fa-microphone"></i>' : 
                '<i class="fas fa-microphone-slash"></i>';
            button.classList.toggle('muted', !enabled);
        }

        // Notify other participants
        this.socket.emit('webrtc_toggle_audio', {
            call_id: this.currentCallId,
            audio_enabled: enabled
        });

        // Update via API
        await this.updateMediaSettings({ audio_enabled: enabled });
    }

    async toggleVideo() {
        if (!this.localStream) return;

        const videoTracks = this.localStream.getVideoTracks();
        const enabled = !this.mediaSettings.video;
        
        videoTracks.forEach(track => {
            track.enabled = enabled;
        });

        this.mediaSettings.video = enabled;

        // Update UI
        const button = document.querySelector('.toggle-video-btn');
        const localVideo = document.getElementById('local-video');
        
        if (button) {
            button.innerHTML = enabled ? 
                '<i class="fas fa-video"></i>' : 
                '<i class="fas fa-video-slash"></i>';
            button.classList.toggle('video-off', !enabled);
        }

        if (localVideo) {
            localVideo.style.display = enabled ? 'block' : 'none';
        }

        // Notify other participants
        this.socket.emit('webrtc_toggle_video', {
            call_id: this.currentCallId,
            video_enabled: enabled
        });

        // Update via API
        await this.updateMediaSettings({ video_enabled: enabled });
    }

    async toggleScreenShare() {
        try {
            const enabled = !this.mediaSettings.screenShare;

            if (enabled) {
                // Start screen sharing
                const screenStream = await navigator.mediaDevices.getDisplayMedia({
                    video: true,
                    audio: true
                });

                // Replace video track
                const videoTrack = screenStream.getVideoTracks()[0];
                const sender = this.peerConnections.forEach(pc => {
                    const senders = pc.getSenders();
                    const videoSender = senders.find(s => 
                        s.track && s.track.kind === 'video'
                    );
                    if (videoSender) {
                        videoSender.replaceTrack(videoTrack);
                    }
                });

                // Handle screen share end
                videoTrack.addEventListener('ended', () => {
                    this.stopScreenShare();
                });

                this.mediaSettings.screenShare = true;
            } else {
                this.stopScreenShare();
            }

            // Update UI
            const button = document.querySelector('.toggle-screen-share-btn');
            if (button) {
                button.classList.toggle('sharing', this.mediaSettings.screenShare);
                button.innerHTML = this.mediaSettings.screenShare ? 
                    '<i class="fas fa-stop"></i> Stop Sharing' : 
                    '<i class="fas fa-desktop"></i> Share Screen';
            }

            // Notify other participants
            this.socket.emit('webrtc_toggle_screen_share', {
                call_id: this.currentCallId,
                screen_share_enabled: this.mediaSettings.screenShare
            });

        } catch (error) {
            console.error('Error toggling screen share:', error);
        }
    }

    async stopScreenShare() {
        // Get camera stream back
        const videoStream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: false 
        });
        
        const videoTrack = videoStream.getVideoTracks()[0];
        
        // Replace screen share with camera
        this.peerConnections.forEach(pc => {
            const senders = pc.getSenders();
            const videoSender = senders.find(s => 
                s.track && s.track.kind === 'video'
            );
            if (videoSender) {
                videoSender.replaceTrack(videoTrack);
            }
        });

        this.mediaSettings.screenShare = false;
    }

    async updateMediaSettings(settings) {
        try {
            const response = await fetch(`/api/webrtc/calls/${this.currentCallId}/participants/${window.currentUserId}/media`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            return await response.json();
        } catch (error) {
            console.error('Error updating media settings:', error);
        }
    }

    handleCallJoined(data) {
        this.currentCallId = data.call_id;
        
        // Set up peer connections for existing participants
        data.participants.forEach(participant => {
            if (participant.user_id !== window.currentUserId) {
                this.createPeerConnection(participant.user_id);
            }
        });
    }

    handleUserJoined(data) {
        if (data.user_id !== window.currentUserId) {
            this.addParticipantToUI(data);
            this.createPeerConnection(data.user_id);
            
            // If we're the initiator, create offer
            if (this.isInitiator) {
                this.createOffer(data.user_id);
            }
        }
    }

    handleUserLeft(data) {
        this.removeParticipantFromUI(data.user_id);
        this.closePeerConnection(data.user_id);
    }

    createPeerConnection(userId) {
        const pc = new RTCPeerConnection({ iceServers: this.iceServers });
        
        // Add local stream
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => {
                pc.addTrack(track, this.localStream);
            });
        }

        // Handle remote stream
        pc.addEventListener('track', (event) => {
            const [remoteStream] = event.streams;
            this.remoteStreams.set(userId, remoteStream);
            this.displayRemoteVideo(userId, remoteStream);
        });

        // Handle ICE candidates
        pc.addEventListener('icecandidate', (event) => {
            if (event.candidate) {
                this.socket.emit('webrtc_ice_candidate', {
                    call_id: this.currentCallId,
                    target_user_id: userId,
                    candidate: event.candidate
                });
            }
        });

        // Handle connection state changes
        pc.addEventListener('connectionstatechange', () => {
            console.log(`Connection state with ${userId}:`, pc.connectionState);
            if (pc.connectionState === 'failed') {
                this.handleConnectionFailure(userId);
            }
        });

        this.peerConnections.set(userId, pc);
        return pc;
    }

    async createOffer(userId) {
        const pc = this.peerConnections.get(userId);
        if (!pc) return;

        try {
            const offer = await pc.createOffer();
            await pc.setLocalDescription(offer);

            this.socket.emit('webrtc_signal', {
                call_id: this.currentCallId,
                target_user_id: userId,
                signal_type: 'offer',
                signal_data: offer
            });
        } catch (error) {
            console.error('Error creating offer:', error);
        }
    }

    async createAnswer(userId, offer) {
        const pc = this.peerConnections.get(userId);
        if (!pc) return;

        try {
            await pc.setRemoteDescription(offer);
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);

            this.socket.emit('webrtc_signal', {
                call_id: this.currentCallId,
                target_user_id: userId,
                signal_type: 'answer',
                signal_data: answer
            });
        } catch (error) {
            console.error('Error creating answer:', error);
        }
    }

    async handleSignalingMessage(data) {
        const { from_user_id, signal_type, signal_data } = data;
        
        if (!this.peerConnections.has(from_user_id)) {
            this.createPeerConnection(from_user_id);
        }

        const pc = this.peerConnections.get(from_user_id);
        
        try {
            switch (signal_type) {
                case 'offer':
                    await this.createAnswer(from_user_id, signal_data);
                    break;
                case 'answer':
                    await pc.setRemoteDescription(signal_data);
                    break;
                default:
                    console.warn('Unknown signal type:', signal_type);
            }
        } catch (error) {
            console.error('Error handling signaling message:', error);
        }
    }

    async handleIceCandidate(data) {
        const { from_user_id, candidate } = data;
        const pc = this.peerConnections.get(from_user_id);
        
        if (pc) {
            try {
                await pc.addIceCandidate(candidate);
            } catch (error) {
                console.error('Error adding ICE candidate:', error);
            }
        }
    }

    handleIncomingCall(data) {
        const { call_info, invitation_data } = data;
        this.showIncomingCallDialog(call_info, invitation_data);
    }

    showCallInterface(callInfo) {
        const callContainer = this.createCallInterface(callInfo);
        document.body.appendChild(callContainer);
        
        // Hide other UI elements if needed
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.display = 'none';
        }
    }

    createCallInterface(callInfo) {
        const container = document.createElement('div');
        container.className = 'webrtc-call-container';
        container.innerHTML = `
            <div class="call-header">
                <div class="call-info">
                    <h3>${callInfo.title || 'Call'}</h3>
                    <span class="call-status">Connected</span>
                    <span class="call-duration" id="call-duration">00:00</span>
                </div>
                <div class="call-participants-count">
                    <i class="fas fa-users"></i>
                    <span id="participants-count">${callInfo.participant_count}</span>
                </div>
            </div>

            <div class="call-content">
                <div class="video-grid" id="video-grid">
                    <div class="video-container local-video-container">
                        <video id="local-video" autoplay muted playsinline></video>
                        <div class="video-overlay">
                            <span class="participant-name">You</span>
                            <div class="media-status">
                                <i class="fas fa-microphone audio-status"></i>
                                <i class="fas fa-video video-status"></i>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="participants-sidebar" id="participants-sidebar">
                    <h4>Participants</h4>
                    <div class="participants-list" id="participants-list">
                        <!-- Participants will be added dynamically -->
                    </div>
                </div>
            </div>

            <div class="call-controls">
                <button class="control-btn toggle-audio-btn" title="Toggle Audio">
                    <i class="fas fa-microphone"></i>
                </button>
                <button class="control-btn toggle-video-btn" title="Toggle Video">
                    <i class="fas fa-video"></i>
                </button>
                <button class="control-btn toggle-screen-share-btn" title="Share Screen">
                    <i class="fas fa-desktop"></i>
                </button>
                <button class="control-btn settings-btn" title="Settings">
                    <i class="fas fa-cog"></i>
                </button>
                <button class="control-btn end-call-btn" title="End Call">
                    <i class="fas fa-phone-slash"></i>
                </button>
            </div>
        `;

        // Start call duration timer
        this.startCallTimer();

        return container;
    }

    showIncomingCallDialog(callInfo, invitationData) {
        const dialog = document.createElement('div');
        dialog.className = 'incoming-call-dialog';
        dialog.innerHTML = `
            <div class="incoming-call-content">
                <div class="caller-info">
                    <div class="caller-avatar">
                        <i class="fas fa-user"></i>
                    </div>
                    <h3>Incoming ${callInfo.call_type} call</h3>
                    <p>${callInfo.title || 'Call from user'}</p>
                </div>
                <div class="call-actions">
                    <button class="btn btn-success accept-call" data-call-id="${callInfo.call_id}">
                        <i class="fas fa-phone"></i> Accept
                    </button>
                    <button class="btn btn-danger decline-call" data-call-id="${callInfo.call_id}">
                        <i class="fas fa-phone-slash"></i> Decline
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(dialog);

        // Handle accept/decline
        dialog.querySelector('.accept-call').addEventListener('click', () => {
            this.joinCall(callInfo.call_id);
            dialog.remove();
        });

        dialog.querySelector('.decline-call').addEventListener('click', () => {
            // Decline call via API
            // Implementation depends on your invitation system
            dialog.remove();
        });

        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (dialog.parentNode) {
                dialog.remove();
            }
        }, 30000);
    }

    addParticipantToUI(participantData) {
        const videoGrid = document.getElementById('video-grid');
        const participantsList = document.getElementById('participants-list');
        
        if (videoGrid) {
            const videoContainer = document.createElement('div');
            videoContainer.className = 'video-container';
            videoContainer.setAttribute('data-user-id', participantData.user_id);
            videoContainer.innerHTML = `
                <video id="video-${participantData.user_id}" autoplay playsinline></video>
                <div class="video-overlay">
                    <span class="participant-name">${participantData.username}</span>
                    <div class="media-status">
                        <i class="fas fa-microphone audio-status"></i>
                        <i class="fas fa-video video-status"></i>
                    </div>
                </div>
            `;
            videoGrid.appendChild(videoContainer);
        }

        if (participantsList) {
            const participantItem = document.createElement('div');
            participantItem.className = 'participant-item';
            participantItem.setAttribute('data-user-id', participantData.user_id);
            participantItem.innerHTML = `
                <div class="participant-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="participant-info">
                    <span class="participant-name">${participantData.username}</span>
                    <div class="participant-status">
                        <i class="fas fa-microphone audio-status"></i>
                        <i class="fas fa-video video-status"></i>
                    </div>
                </div>
            `;
            participantsList.appendChild(participantItem);
        }
    }

    removeParticipantFromUI(userId) {
        const videoContainer = document.querySelector(`[data-user-id="${userId}"]`);
        const participantItem = document.querySelector(`.participant-item[data-user-id="${userId}"]`);
        
        if (videoContainer) {
            videoContainer.remove();
        }
        if (participantItem) {
            participantItem.remove();
        }
    }

    displayRemoteVideo(userId, stream) {
        const video = document.getElementById(`video-${userId}`);
        if (video) {
            video.srcObject = stream;
        }
    }

    updateParticipantAudio(userId, enabled) {
        const audioStatus = document.querySelector(`[data-user-id="${userId}"] .audio-status`);
        if (audioStatus) {
            audioStatus.className = enabled ? 'fas fa-microphone audio-status' : 'fas fa-microphone-slash audio-status muted';
        }
    }

    updateParticipantVideo(userId, enabled) {
        const videoStatus = document.querySelector(`[data-user-id="${userId}"] .video-status`);
        const video = document.getElementById(`video-${userId}`);
        
        if (videoStatus) {
            videoStatus.className = enabled ? 'fas fa-video video-status' : 'fas fa-video-slash video-status video-off';
        }
        
        if (video) {
            video.style.display = enabled ? 'block' : 'none';
        }
    }

    updateParticipantScreenShare(userId, enabled) {
        // Handle screen share UI updates
        const videoContainer = document.querySelector(`[data-user-id="${userId}"]`);
        if (videoContainer) {
            videoContainer.classList.toggle('screen-sharing', enabled);
        }
    }

    closePeerConnection(userId) {
        const pc = this.peerConnections.get(userId);
        if (pc) {
            pc.close();
            this.peerConnections.delete(userId);
        }
        this.remoteStreams.delete(userId);
    }

    handleConnectionFailure(userId) {
        console.warn(`Connection failed with user ${userId}`);
        this.showError(`Connection lost with participant ${userId}`);
    }

    startCallTimer() {
        let seconds = 0;
        const timer = setInterval(() => {
            if (!this.currentCallId) {
                clearInterval(timer);
                return;
            }
            
            seconds++;
            const minutes = Math.floor(seconds / 60);
            const remainingSeconds = seconds % 60;
            const display = `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
            
            const durationElement = document.getElementById('call-duration');
            if (durationElement) {
                durationElement.textContent = display;
            }
        }, 1000);
    }

    cleanup() {
        // Close all peer connections
        this.peerConnections.forEach((pc, userId) => {
            this.closePeerConnection(userId);
        });

        // Stop local stream
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }

        // Remove call interface
        const callContainer = document.querySelector('.webrtc-call-container');
        if (callContainer) {
            callContainer.remove();
        }

        // Show main content
        const mainContent = document.querySelector('.main-content');
        if (mainContent) {
            mainContent.style.display = 'block';
        }

        // Reset state
        this.currentCallId = null;
        this.isInitiator = false;
        this.participants.clear();
        this.remoteStreams.clear();
    }

    showError(message) {
        // Show error notification
        const errorDiv = document.createElement('div');
        errorDiv.className = 'webrtc-error alert alert-danger';
        errorDiv.textContent = message;
        
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentNode) {
                errorDiv.remove();
            }
        }, 5000);
    }

    generatePeerId() {
        return 'peer_' + Math.random().toString(36).substr(2, 9);
    }

    generateSessionId() {
        return 'session_' + Math.random().toString(36).substr(2, 9);
    }
}

// Initialize WebRTC manager when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    if (typeof window.webrtcManager === 'undefined') {
        window.webrtcManager = new WebRTCCallManager();
    }
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebRTCCallManager;
}
