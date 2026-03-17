import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, TextInput, TouchableOpacity, FlatList, KeyboardAvoidingView, Platform, ActivityIndicator, Image } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRoute } from '@react-navigation/native';
import * as ImagePicker from 'expo-image-picker';
import api from '../../services/api';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme/dark';

interface Message { role: 'user' | 'assistant'; content: string; attachment_url?: string; attachment_type?: string; isTyping?: boolean; }

export default function MaxChatScreen() {
    const route = useRoute<any>();
    const initSchedule = route.params?.initSchedule;
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedImage, setSelectedImage] = useState<string | null>(null);
    const flatListRef = useRef<FlatList>(null);
    const initScheduleHandled = useRef(false);

    const showTyping = () => setMessages(prev => [...prev.filter(m => !m.isTyping), { role: 'assistant', content: '', isTyping: true }]);
    const hideTyping = () => setMessages(prev => prev.filter(m => !m.isTyping));

    useEffect(() => {
        if (initSchedule) {
            // If starting a schedule, send the init message first, then loadHistory will run on complete
            initScheduleHandled.current = initSchedule;
            const maxxLabel = initSchedule.charAt(0).toUpperCase() + initSchedule.slice(1).replace('max', 'Max');
            sendMessageWithContext(`I want to start my ${maxxLabel} schedule.`, initSchedule);
        } else {
            loadHistory();
        }
    }, []);

    const loadHistory = async () => { try { const { messages: history } = await api.getChatHistory(); setMessages(history || []); } catch (e) { console.error(e); } };

    const handlePickImage = async () => {
        const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ['images'], allowsEditing: true, quality: 0.8 });
        if (!result.canceled) setSelectedImage(result.assets[0].uri);
    };

    const sendMessageWithContext = async (msg: string, initContext?: string) => {
        if (!msg.trim() || loading) return;
        setLoading(true);
        showTyping();
        try {
            await api.sendChatMessage(msg, undefined, undefined, initContext);
            hideTyping();
            await loadHistory();
        } catch (e: any) {
            console.error('sendMessageWithContext error:', e?.response?.data || e?.message || e);
            hideTyping();
            setMessages(prev => [...prev, { role: 'assistant', content: 'sorry, something went wrong. try again.' }]);
        } finally {
            setLoading(false);
        }
    };

    const sendMessage = async () => {
        if ((!input.trim() && !selectedImage) || loading) return;
        const userContent = input.trim();
        let attachmentUrl: string | undefined; let attachmentType: string | undefined;
        setLoading(true); setInput(''); setSelectedImage(null);
        // Optimistic: show user message immediately
        setMessages(prev => [...prev, { role: 'user', content: userContent }]);
        showTyping();
        try {
            if (selectedImage) {
                setUploading(true);
                const formData = new FormData();
                const filename = selectedImage.split('/').pop() || 'upload.jpg';
                const match = /\.(\w+)$/.exec(filename);
                formData.append('file', { uri: selectedImage, name: filename, type: match ? `image/${match[1]}` : 'image' } as any);
                const uploadRes = await api.uploadChatFile(formData);
                attachmentUrl = uploadRes.url; attachmentType = 'image'; setUploading(false);
            }
            await api.sendChatMessage(userContent, attachmentUrl, attachmentType, initSchedule);
            hideTyping();
            await loadHistory();
        } catch (e) {
            console.error(e);
            hideTyping();
            setMessages(prev => [...prev, { role: 'assistant', content: 'sorry, something went wrong.' }]);
        } finally { setLoading(false); setUploading(false); }
    };

    const TypingDots = () => {
        const [dots, setDots] = React.useState('');
        React.useEffect(() => {
            const id = setInterval(() => setDots(d => d.length >= 3 ? '' : d + '.'), 400);
            return () => clearInterval(id);
        }, []);
        return <Text style={styles.typingText}>typing{dots}</Text>;
    };

    const renderMessage = ({ item }: { item: Message }) => {
        const hasContent = item.content?.trim();
        const hasImage = item.attachment_url && item.attachment_type === 'image';
        if (item.isTyping) {
            return (
                <View style={[styles.messageRow]}>
                    <View style={[styles.bubble, styles.assistantBubble, styles.typingBubble]}>
                        <TypingDots />
                    </View>
                </View>
            );
        }
        if (!hasContent && !hasImage) return null;
        return (
            <View style={[styles.messageRow, item.role === 'user' && styles.userMessageRow]}>
                <View style={[styles.bubble, item.role === 'user' ? styles.userBubble : styles.assistantBubble]}>
                    {hasContent ? <Text style={[styles.messageText, item.role === 'user' && styles.userMessageText]}>{item.content}</Text> : null}
                    {hasImage && (
                        <Image source={{ uri: api.resolveAttachmentUrl(item.attachment_url) }} style={styles.attachmentImage} resizeMode="cover" />
                    )}
                </View>
            </View>
        );
    };

    const ListEmpty = () => (
        <View style={styles.emptyState}>
            <Text style={styles.emptyTitle}>Start a conversation</Text>
            <Text style={styles.emptySubtitle}>Ask Max about lookmaxxing, routines, or anything else.</Text>
        </View>
    );

    return (
        <View style={styles.container}>
            {/* Faint chat icon watermark in center background */}
            <View style={styles.watermarkWrap} pointerEvents="none">
                <Ionicons name="chatbubbles" size={140} color={colors.textMuted} style={styles.watermarkIcon} />
            </View>

            <KeyboardAvoidingView style={styles.keyboardView} behavior={Platform.OS === 'ios' ? 'padding' : 'height'} keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}>
                <View style={styles.header}>
                    <Text style={styles.title}>Max</Text>
                    <Text style={styles.subtitle}>Your lookmaxxing coach</Text>
                </View>

                <FlatList
                    ref={flatListRef}
                    data={messages}
                    renderItem={renderMessage}
                    keyExtractor={(item, i) => item.isTyping ? 'typing' : i.toString()}
                    contentContainerStyle={[styles.messageList, messages.length === 0 && styles.messageListEmpty]}
                    onContentSizeChange={() => flatListRef.current?.scrollToEnd()}
                    showsVerticalScrollIndicator={false}
                    ListEmptyComponent={ListEmpty}
                />

                <View style={styles.outerInputContainer}>
                    {selectedImage && (
                        <View style={styles.imagePreviewContainer}>
                            <Image source={{ uri: selectedImage }} style={styles.imagePreview} />
                            <TouchableOpacity style={styles.removeImageBtn} onPress={() => setSelectedImage(null)}>
                                <Ionicons name="close-circle" size={22} color={colors.error} />
                            </TouchableOpacity>
                            {uploading && <View style={styles.uploadOverlay}><ActivityIndicator color={colors.buttonText} /></View>}
                        </View>
                    )}
                    <View style={styles.inputContainer}>
                        <TouchableOpacity style={styles.attachButton} onPress={handlePickImage} disabled={loading || uploading}>
                            <Ionicons name="add-circle-outline" size={26} color={colors.textMuted} />
                        </TouchableOpacity>
                        <TextInput
                            style={styles.input}
                            placeholder="Ask Max anything..."
                            placeholderTextColor={colors.textMuted}
                            value={input}
                            onChangeText={setInput}
                            multiline
                            editable={!loading && !uploading}
                        />
                        <TouchableOpacity
                            style={[styles.sendButton, (!input.trim() && !selectedImage) && styles.disabledButton]}
                            onPress={sendMessage}
                            disabled={(!input.trim() && !selectedImage) || loading || uploading}
                        >
                            {loading || uploading ? <ActivityIndicator size="small" color={colors.buttonText} /> : <Ionicons name="send" size={18} color={colors.buttonText} />}
                        </TouchableOpacity>
                    </View>
                </View>
            </KeyboardAvoidingView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    keyboardView: { flex: 1 },
    watermarkWrap: {
        ...StyleSheet.absoluteFillObject,
        justifyContent: 'center',
        alignItems: 'center',
    },
    watermarkIcon: {
        opacity: 0.07,
    },
    header: {
        paddingTop: 64,
        paddingHorizontal: spacing.lg,
        paddingBottom: spacing.lg,
        borderBottomWidth: 1,
        borderBottomColor: colors.border,
        backgroundColor: colors.card,
    },
    title: { fontSize: 26, fontWeight: '700', color: colors.foreground, letterSpacing: -0.5 },
    subtitle: { fontSize: 14, color: colors.textMuted, marginTop: 4 },
    messageList: { padding: spacing.lg, paddingBottom: spacing.xl },
    messageListEmpty: { flexGrow: 1 },
    messageRow: { flexDirection: 'row', marginBottom: spacing.md, paddingHorizontal: 4 },
    userMessageRow: { justifyContent: 'flex-end' },
    bubble: {
        maxWidth: '82%',
        paddingHorizontal: 16,
        paddingVertical: 12,
        borderRadius: 18,
        ...shadows.sm,
    },
    userBubble: {
        backgroundColor: colors.foreground,
        borderBottomRightRadius: 6,
        ...shadows.md,
    },
    assistantBubble: {
        backgroundColor: colors.card,
        borderBottomLeftRadius: 6,
        borderWidth: 1,
        borderColor: colors.border,
    },
    messageText: { fontSize: 15, lineHeight: 22, color: colors.foreground },
    userMessageText: { color: colors.buttonText },
    typingBubble: { paddingVertical: 10, paddingHorizontal: 16 },
    typingText: { fontSize: 14, color: colors.textMuted, fontStyle: 'italic' },
    attachmentImage: { width: 220, height: 160, borderRadius: 12, marginTop: spacing.sm },
    emptyState: { flex: 1, justifyContent: 'center', alignItems: 'center', paddingHorizontal: spacing.xl },
    emptyTitle: { fontSize: 18, fontWeight: '600', color: colors.foreground, marginBottom: 8 },
    emptySubtitle: { fontSize: 14, color: colors.textMuted, textAlign: 'center', lineHeight: 20 },
    outerInputContainer: {
        padding: spacing.md,
        paddingBottom: spacing.lg,
        borderTopWidth: 1,
        borderTopColor: colors.border,
        backgroundColor: colors.background,
    },
    imagePreviewContainer: { position: 'relative', marginBottom: spacing.sm, alignSelf: 'flex-start' },
    imagePreview: { width: 80, height: 80, borderRadius: 12 },
    removeImageBtn: { position: 'absolute', top: -6, right: -6, backgroundColor: colors.card, borderRadius: 14, ...shadows.sm },
    uploadOverlay: { ...StyleSheet.absoluteFillObject, backgroundColor: 'rgba(0,0,0,0.5)', justifyContent: 'center', alignItems: 'center', borderRadius: 12 },
    inputContainer: {
        flexDirection: 'row',
        alignItems: 'flex-end',
        backgroundColor: colors.card,
        borderRadius: 24,
        paddingHorizontal: 12,
        paddingVertical: 8,
        borderWidth: 1,
        borderColor: colors.border,
        ...shadows.sm,
    },
    attachButton: { padding: 6, marginRight: 4 },
    input: { flex: 1, color: colors.textPrimary, fontSize: 15, paddingVertical: 10, paddingHorizontal: 8, maxHeight: 100 },
    sendButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: colors.foreground, justifyContent: 'center', alignItems: 'center', marginLeft: 8, ...shadows.sm },
    disabledButton: { opacity: 0.35 },
});
