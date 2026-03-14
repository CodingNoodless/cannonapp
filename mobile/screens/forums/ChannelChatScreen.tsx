import React, { useEffect, useState, useRef, useCallback } from 'react';
import { View, Text, StyleSheet, FlatList, TextInput, TouchableOpacity, KeyboardAvoidingView, Platform, ActivityIndicator, Image } from 'react-native';
import { useNavigation, useRoute, useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme/dark';

interface Message {
    id: string;
    channel_id: string;
    user_id: string;
    user_email: string;
    username?: string;
    content: string;
    attachment_url?: string;
    attachment_type?: string;
    created_at: string;
    is_admin: boolean;
    parent_id?: string;
    reactions?: Record<string, string[]>;
}

export default function ChannelChatScreen() {
    const navigation = useNavigation();
    const insets = useSafeAreaInsets();
    const route = useRoute<any>();
    const { channelId, channelName } = route.params;
    const [isAdminOnly, setIsAdminOnly] = useState(route.params.isAdminOnly || false);
    const { user } = useAuth();
    const [messages, setMessages] = useState<Message[]>([]);
    const [loading, setLoading] = useState(true);
    const [messageText, setMessageText] = useState('');
    const [sending, setSending] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [isSearching, setIsSearching] = useState(false);
    const [replyingTo, setReplyingTo] = useState<Message | null>(null);
    const flatListRef = useRef<FlatList>(null);
    const isAdmin = user?.is_admin || false;
    const currentUserId = user?.id;
    const canPostTopLevel = !isAdminOnly || isAdmin;

    useFocusEffect(useCallback(() => {
        loadMessages();
        const interval = !isSearching ? setInterval(loadMessages, 5000) : null;
        return () => interval && clearInterval(interval);
    }, [channelId, searchQuery, isSearching]));

    const loadMessages = async () => {
        try { const data = await api.getChannelMessages(channelId, 50, searchQuery); setMessages(data.messages || []); if (data.is_admin_only !== undefined) setIsAdminOnly(data.is_admin_only); }
        catch (e) { console.error(e); } finally { setLoading(false); }
    };

    const handlePickImage = async () => { const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], allowsEditing: true, quality: 0.8 }); if (!result.canceled) setSelectedImage(result.assets[0].uri); };

    const handleSendMessage = async () => {
        if ((!messageText.trim() && !selectedImage) || sending) return;
        if (isAdminOnly && !isAdmin && !replyingTo) return;
        setSending(true); let attachmentUrl = undefined; let attachmentType = undefined;
        try {
            if (selectedImage) {
                setUploading(true); const formData = new FormData(); const filename = selectedImage.split('/').pop() || 'upload.jpg'; const match = /\.(\w+)$/.exec(filename);
                formData.append('file', { uri: selectedImage, name: filename, type: match ? `image/${match[1]}` : 'image' } as any);
                const uploadRes = await api.uploadChatFile(formData); attachmentUrl = uploadRes.url; attachmentType = 'image'; setUploading(false);
            }
            const result = await api.sendChannelMessage(channelId, messageText.trim() || '', replyingTo?.id, attachmentUrl, attachmentType);
            if (result.message) setMessages(prev => [...prev, result.message]);
            setMessageText(''); setReplyingTo(null); setSelectedImage(null);
            setTimeout(() => flatListRef.current?.scrollToEnd({ animated: true }), 100);
        } catch (e) { console.error(e); } finally { setSending(false); setUploading(false); }
    };

    const handleToggleReaction = async (messageId: string, emoji: string) => {
        try { const result = await api.toggleReaction(channelId, messageId, emoji); setMessages(prev => prev.map(m => m.id === messageId ? { ...m, reactions: result.reactions } : m)); } catch (e) { console.error(e); }
    };

    const formatTime = (dateString: string) =>
        new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    const getDisplayName = (message: Message) => {
        if (message.username && message.username.trim().length > 0) return message.username;
        return message.user_email.split('@')[0];
    };

    const renderMessage = ({ item, index }: { item: Message; index: number }) => {
        const prevMessage = index > 0 ? messages[index - 1] : null;
        const isSameUser = prevMessage && prevMessage.user_id === item.user_id;
        const isCurrentUser = item.user_id === currentUserId;
        const timeDiff = prevMessage ? (new Date(item.created_at).getTime() - new Date(prevMessage.created_at).getTime()) / 60000 : 999;
        const showFullHeader = !isSameUser || timeDiff > 5 || item.parent_id;
        const repliedMessage = item.parent_id ? messages.find(m => m.id === item.parent_id) : null;

        return (
            <View style={[styles.messageWrapper, isCurrentUser ? styles.userMessageWrapper : styles.otherMessageWrapper, !showFullHeader && styles.compactMessage]}>
                {repliedMessage && (
                    <View style={[styles.replyContext, isCurrentUser ? styles.userReplyContext : styles.otherReplyContext]}>
                        {!isCurrentUser && <View style={styles.replyLine} />}
                        <Text style={styles.replyContextText} numberOfLines={1}>
                            <Text style={styles.replyContextUser}>{getDisplayName(repliedMessage)}: </Text>
                            {repliedMessage.content}
                        </Text>
                        {isCurrentUser && <View style={[styles.replyLine, { borderLeftWidth: 0, borderRightWidth: 2, marginRight: 0, marginLeft: 8, borderTopRightRadius: 4, borderTopLeftRadius: 0 }]} />}
                    </View>
                )}
                <View style={styles.messageHeaderRow}>
                    {isCurrentUser ? (
                        <>
                            <View style={styles.userMessageSpacer} />
                            <View style={styles.userMessageContent}>
                                <View style={[styles.bubble, styles.userBubble, item.is_admin && styles.adminHighlight]}>
                                    {item.content ? <Text style={[styles.messageText, styles.userMessageText]}>{item.content}</Text> : null}
                                    {item.attachment_url && item.attachment_type === 'image' && <Image source={{ uri: api.resolveAttachmentUrl(item.attachment_url) }} style={styles.attachmentImage} resizeMode="cover" />}
                                </View>
                                <Text style={[styles.timestamp, styles.userTimestamp]}>{formatTime(item.created_at)}</Text>
                                {renderReactions(item)}
                            </View>
                        </>
                    ) : (
                        <>
                            {showFullHeader && (
                                <View style={styles.avatarMini}>
                                    <Text style={styles.avatarInitial}>{getDisplayName(item)[0]?.toUpperCase()}</Text>
                                </View>
                            )}
                            {!showFullHeader && <View style={styles.avatarSpacer} />}
                            <View style={[styles.messageContentArea, styles.otherContentArea]}>
                                <View style={[styles.bubble, styles.otherBubble, item.is_admin && styles.adminHighlight]}>
                                    {showFullHeader && (
                                        <View style={styles.nameRow}>
                                            <Text style={[styles.userName, item.is_admin && styles.adminName]}>
                                                {getDisplayName(item)}
                                            </Text>
                                            {item.is_admin && (
                                                <View style={styles.adminTag}>
                                                    <Text style={styles.adminTagText}>ADMIN</Text>
                                                </View>
                                            )}
                                        </View>
                                    )}
                                    {item.content ? <Text style={styles.messageText}>{item.content}</Text> : null}
                                    {item.attachment_url && item.attachment_type === 'image' && <Image source={{ uri: api.resolveAttachmentUrl(item.attachment_url) }} style={styles.attachmentImage} resizeMode="cover" />}
                                </View>
                                <Text style={[styles.timestamp, styles.otherTimestamp]}>{formatTime(item.created_at)}</Text>
                                {renderReactions(item)}
                            </View>
                        </>
                    )}
                </View>
                <View style={[styles.messageActions, isCurrentUser ? styles.userMessageActions : styles.otherMessageActions]}>
                    <TouchableOpacity onPress={() => setReplyingTo(item)} style={styles.actionBtn}><Ionicons name="arrow-undo" size={14} color={colors.textMuted} /></TouchableOpacity>
                    {!isCurrentUser && <TouchableOpacity onPress={() => handleToggleReaction(item.id, '\uD83D\uDD25')} style={styles.actionBtn}><Ionicons name="flash" size={14} color={colors.textMuted} /></TouchableOpacity>}
                </View>
            </View>
        );
    };

    const renderReactions = (message: Message) => {
        if (!message.reactions || Object.keys(message.reactions).length === 0) return null;
        return (
            <View style={styles.reactionsRow}>
                {Object.entries(message.reactions).map(([emoji, userIds]) => {
                    const hasReacted = currentUserId ? userIds.includes(currentUserId) : false;
                    return (
                        <TouchableOpacity key={emoji} onPress={() => handleToggleReaction(message.id, emoji)} style={[styles.reactionBadge, hasReacted && styles.reactionBadgeActive]}>
                            <Text style={styles.reactionEmoji}>{emoji}</Text>
                            <Text style={[styles.reactionCount, hasReacted && styles.reactionCountActive]}>{userIds.length}</Text>
                        </TouchableOpacity>
                    );
                })}
            </View>
        );
    };

    if (loading && messages.length === 0) return <View style={[styles.container, styles.center]}><ActivityIndicator size="large" color={colors.foreground} /></View>;

    const placeholderText = replyingTo
        ? `Replying to ${getDisplayName(replyingTo)}`
        : isAdminOnly && !isAdmin
        ? 'Only admins can start announcements'
        : `Message #${channelName}`;

    return (
        <View style={styles.container}>
            <KeyboardAvoidingView style={styles.keyboardView} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
                <View style={[styles.header, { paddingTop: insets.top + spacing.sm, paddingBottom: spacing.md }]}>
                    <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
                        <Ionicons name="chevron-back" size={24} color={colors.foreground} />
                    </TouchableOpacity>
                    {!isSearching ? (
                        <>
                            <View style={styles.headerCenter}>
                                <Text style={styles.channelName} numberOfLines={1}>{channelName}</Text>
                                <Text style={styles.channelHint}>Channel</Text>
                            </View>
                            <TouchableOpacity onPress={() => setIsSearching(true)} style={styles.headerAction} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
                                <Ionicons name="search" size={22} color={colors.textMuted} />
                            </TouchableOpacity>
                        </>
                    ) : (
                        <View style={styles.searchBar}>
                            <Ionicons name="search" size={18} color={colors.textMuted} style={{ marginRight: spacing.sm }} />
                            <TextInput style={styles.searchInput} placeholder="Search messages..." placeholderTextColor={colors.textMuted} value={searchQuery} onChangeText={setSearchQuery} autoFocus />
                            <TouchableOpacity onPress={() => { setIsSearching(false); setSearchQuery(''); }}><Text style={styles.cancelText}>Cancel</Text></TouchableOpacity>
                        </View>
                    )}
                </View>

                <FlatList ref={flatListRef} data={messages} renderItem={renderMessage} keyExtractor={(item) => item.id} contentContainerStyle={[styles.messagesList, { paddingBottom: insets.bottom + 24 }]} style={styles.messagesListContainer} onContentSizeChange={() => { if (!isSearching) flatListRef.current?.scrollToEnd({ animated: false }); }} showsVerticalScrollIndicator={false}
                    ListEmptyComponent={
                    <View style={styles.emptyState}>
                        {isSearching ? (
                            <Text style={styles.welcomeSubtitle}>No messages found for "{searchQuery}"</Text>
                        ) : (
                            <>
                                <View style={styles.emptyStateIcon}><Ionicons name="chatbubble-ellipses-outline" size={40} color={colors.textMuted} /></View>
                                <Text style={styles.welcomeTitle}>{channelName}</Text>
                                <Text style={styles.welcomeSubtitle}>No messages yet. Be the first to say something.</Text>
                            </>
                        )}
                    </View>
                } />

                {isAdminOnly && !isAdmin && !replyingTo && !isSearching && (
                    <View style={styles.restrictedInfo}><Ionicons name="information-circle" size={18} color={colors.textMuted} /><Text style={styles.restrictedInfoText}>Only admins can post announcements. Reply to comment.</Text></View>
                )}

                {!isSearching && (isAdmin || !isAdminOnly || replyingTo) && (
                    <View style={[styles.inputWrapper, { paddingBottom: Math.max(insets.bottom, spacing.sm) }]}>
                        {replyingTo && (
                            <View style={styles.replyPreview}>
                                <Text style={styles.replyPreviewText} numberOfLines={1}>
                                    Replying to{' '}
                                    <Text style={{ fontWeight: '600' }}>{getDisplayName(replyingTo)}</Text>
                                </Text>
                                <TouchableOpacity onPress={() => setReplyingTo(null)}>
                                    <Ionicons name="close-circle" size={18} color={colors.textMuted} />
                                </TouchableOpacity>
                            </View>
                        )}
                        {selectedImage && <View style={styles.imagePreviewContainer}><Image source={{ uri: selectedImage }} style={styles.imagePreview} /><TouchableOpacity style={styles.removeImageBtn} onPress={() => setSelectedImage(null)}><Ionicons name="close-circle" size={22} color={colors.error} /></TouchableOpacity>{uploading && <View style={styles.uploadOverlay}><ActivityIndicator color={colors.buttonText} /></View>}</View>}
                        <View style={styles.inputContainer}>
                            <TouchableOpacity style={styles.attachBtn} onPress={handlePickImage} disabled={uploading}><Ionicons name="add-circle" size={24} color={colors.textMuted} /></TouchableOpacity>
                            <TextInput style={styles.input} placeholder={placeholderText} placeholderTextColor={colors.textMuted} value={messageText} onChangeText={setMessageText} multiline editable={(canPostTopLevel || !!replyingTo) && !uploading} />
                            <TouchableOpacity style={[styles.sendBtn, (messageText.trim() || selectedImage) && (canPostTopLevel || !!replyingTo) && styles.sendBtnActive, (!messageText.trim() && !selectedImage || (!canPostTopLevel && !replyingTo)) && styles.disabledBtn]} onPress={handleSendMessage} disabled={(!messageText.trim() && !selectedImage) || sending || uploading || (!canPostTopLevel && !replyingTo)}>
                                {uploading || sending ? <ActivityIndicator size="small" color={colors.buttonText} /> : <Ionicons name="send" size={18} color={(messageText.trim() || selectedImage) && (canPostTopLevel || !!replyingTo) ? colors.buttonText : colors.textMuted} />}
                            </TouchableOpacity>
                        </View>
                    </View>
                )}
            </KeyboardAvoidingView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    center: { justifyContent: 'center', alignItems: 'center' },
    keyboardView: { flex: 1 },
    header: { backgroundColor: colors.card, flexDirection: 'row', alignItems: 'center', paddingHorizontal: spacing.md, borderBottomWidth: 1, borderBottomColor: colors.border, ...shadows.sm },
    backButton: { marginRight: spacing.sm },
    headerCenter: { flex: 1, minWidth: 0 },
    channelName: { fontSize: 18, fontWeight: '700', color: colors.foreground },
    channelHint: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    headerAction: { padding: spacing.xs },
    searchBar: { flex: 1, flexDirection: 'row', alignItems: 'center', backgroundColor: colors.surface, borderRadius: 10, paddingHorizontal: spacing.sm, height: 40 },
    searchInput: { flex: 1, color: colors.textPrimary, fontSize: 15, paddingVertical: 8, marginRight: spacing.sm },
    cancelText: { color: colors.info, fontWeight: '600', fontSize: 15 },
    messagesListContainer: { backgroundColor: colors.surface },
    messagesList: { paddingLeft: spacing.md, paddingRight: spacing.lg, paddingTop: spacing.lg, paddingBottom: spacing.lg },
    messageWrapper: { marginBottom: spacing.lg, width: '100%' },
    userMessageWrapper: { alignItems: 'flex-end', paddingRight: 2 },
    otherMessageWrapper: { alignItems: 'flex-start' },
    compactMessage: { marginBottom: spacing.sm },
    bubble: { paddingHorizontal: 14, paddingVertical: 12, borderRadius: 18, maxWidth: '100%' },
    userBubble: { backgroundColor: colors.foreground, borderBottomRightRadius: 6, ...shadows.md },
    otherBubble: { backgroundColor: colors.card, borderBottomLeftRadius: 6, borderWidth: 1, borderColor: colors.border, ...shadows.sm },
    adminHighlight: { borderWidth: 1.5, borderColor: colors.warning, backgroundColor: 'rgba(255, 159, 10, 0.08)' },
    replyContext: { flexDirection: 'row', alignItems: 'center', marginBottom: 6, paddingLeft: 10, paddingVertical: 6, paddingRight: 8, backgroundColor: colors.surface, borderRadius: 10, marginHorizontal: 2 },
    userReplyContext: { alignSelf: 'flex-end', marginRight: 2, marginLeft: 0 },
    otherReplyContext: { alignSelf: 'flex-start', marginLeft: 44 },
    replyLine: { width: 3, minHeight: 24, borderRadius: 2, backgroundColor: colors.info, marginRight: 10 },
    replyContextText: { color: colors.textSecondary, fontSize: 13, flex: 1 },
    replyContextUser: { fontWeight: '600', color: colors.foreground },
    messageHeaderRow: { flexDirection: 'row', width: '100%', alignItems: 'flex-end' },
    userMessageSpacer: { flex: 1, minWidth: 0 },
    userMessageContent: { flexShrink: 0, maxWidth: '80%', alignItems: 'flex-end' },
    avatarMini: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.foreground, justifyContent: 'center', alignItems: 'center', marginRight: spacing.sm },
    avatarInitial: { color: colors.buttonText, fontWeight: '700', fontSize: 14 },
    avatarSpacer: { width: 44, marginRight: 0 },
    messageContentArea: { flexShrink: 1, maxWidth: '100%' },
    otherContentArea: { flex: 1 },
    nameRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 6 },
    userName: { color: colors.foreground, fontWeight: '700', fontSize: 13 },
    adminName: { color: colors.warning },
    adminTag: { backgroundColor: colors.warning, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 6, marginLeft: 6 },
    adminTagText: { color: colors.background, fontSize: 10, fontWeight: '700' },
    timestamp: { color: colors.textMuted, fontSize: 11, marginTop: 6 },
    userTimestamp: { alignSelf: 'flex-end', marginRight: 4 },
    otherTimestamp: { alignSelf: 'flex-start', marginLeft: 4 },
    messageText: { color: colors.foreground, fontSize: 15, lineHeight: 22 },
    userMessageText: { color: colors.buttonText },
    attachmentImage: { width: '100%', aspectRatio: 1.33, borderRadius: 12, marginTop: spacing.sm, backgroundColor: colors.surface, maxWidth: 260 },
    messageActions: { flexDirection: 'row', gap: spacing.sm, marginTop: 6, alignItems: 'center' },
    userMessageActions: { alignSelf: 'flex-end' },
    otherMessageActions: { paddingLeft: 52 },
    actionBtn: { padding: 6 },
    reactionsRow: { flexDirection: 'row', flexWrap: 'wrap', marginTop: 8, gap: 6 },
    reactionBadge: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.surface, paddingHorizontal: 10, paddingVertical: 5, borderRadius: 12, borderWidth: 1, borderColor: colors.border },
    reactionBadgeActive: { backgroundColor: colors.accentMuted, borderColor: colors.foreground },
    reactionEmoji: { fontSize: 13 },
    reactionCount: { fontSize: 11, color: colors.textSecondary, marginLeft: 4 },
    reactionCountActive: { color: colors.foreground, fontWeight: '600' },
    emptyState: { padding: spacing.xxl, alignItems: 'center' },
    emptyStateIcon: { width: 72, height: 72, borderRadius: 36, backgroundColor: colors.surface, justifyContent: 'center', alignItems: 'center', marginBottom: spacing.lg },
    welcomeTitle: { fontSize: 20, fontWeight: '700', color: colors.foreground, textAlign: 'center', marginBottom: spacing.sm },
    welcomeSubtitle: { fontSize: 14, color: colors.textMuted, textAlign: 'center', lineHeight: 20 },
    inputWrapper: { paddingHorizontal: spacing.md, paddingTop: spacing.sm, backgroundColor: colors.background, borderTopWidth: 1, borderTopColor: colors.border },
    replyPreview: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', backgroundColor: colors.surface, paddingVertical: 10, paddingHorizontal: spacing.md, borderRadius: 12, marginBottom: spacing.sm, borderLeftWidth: 3, borderLeftColor: colors.info },
    replyPreviewText: { color: colors.textSecondary, fontSize: 13, flex: 1 },
    imagePreviewContainer: { position: 'relative', marginBottom: spacing.sm, alignSelf: 'flex-start' },
    imagePreview: { width: 88, height: 88, borderRadius: 12 },
    removeImageBtn: { position: 'absolute', top: -6, right: -6, backgroundColor: colors.card, borderRadius: 14, ...shadows.sm },
    uploadOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', borderRadius: borderRadius.md },
    inputContainer: { flexDirection: 'row', alignItems: 'flex-end', backgroundColor: colors.card, borderRadius: 22, paddingHorizontal: spacing.sm, paddingVertical: 6, paddingRight: 4, borderWidth: 1, borderColor: colors.border, ...shadows.sm },
    attachBtn: { padding: 8, marginRight: 4 },
    input: { flex: 1, color: colors.textPrimary, paddingHorizontal: spacing.sm, fontSize: 15, maxHeight: 100, minHeight: 38 },
    sendBtn: { width: 36, height: 36, borderRadius: 18, justifyContent: 'center', alignItems: 'center' },
    sendBtnActive: { backgroundColor: colors.foreground },
    disabledBtn: { opacity: 0.4 },
    restrictedInfo: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', padding: spacing.md, backgroundColor: colors.surface, borderTopWidth: 1, borderTopColor: colors.border, gap: 8 },
    restrictedInfoText: { color: colors.textMuted, fontSize: 13, fontWeight: '500' },
});
