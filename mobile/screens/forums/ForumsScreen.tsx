import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import { useNavigation, useFocusEffect } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import api from '../../services/api';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme/dark';

export default function ForumsScreen() {
    const navigation = useNavigation<any>();
    const insets = useSafeAreaInsets();
    const [forums, setForums] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [searchQuery, setSearchQuery] = useState('');
    const [activeChannelId, setActiveChannelId] = useState<string | null>(null);

    useFocusEffect(React.useCallback(() => { loadForums(); }, [searchQuery]));

    const loadForums = async () => {
        try { setLoading(true); const { forums: data } = await api.getChannels(searchQuery); setForums(data || []); if (data?.length > 0 && !activeChannelId) setActiveChannelId(data[0].id); }
        catch (e) { console.error(e); } finally { setLoading(false); }
    };

    const handleChannelPress = (item: any) => {
        setActiveChannelId(item.id);
        navigation.navigate('ChannelChat', { channelId: item.id, channelName: item.name, isAdminOnly: item.is_admin_only });
    };

    const categorizedForums = [
        { title: 'Official', key: 'OFFICIAL', channels: forums.filter(f => f.name.toLowerCase().includes('announce') || f.name.toLowerCase().includes('welcome')) },
        { title: 'Community', key: 'COMMUNITY', channels: forums.filter(f => !f.name.toLowerCase().includes('announce') && !f.name.toLowerCase().includes('welcome')) },
    ];

    return (
        <View style={[styles.container, { paddingTop: insets.top }]}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Forums</Text>
                <Text style={styles.headerSubtitle}>Channels and discussions</Text>
                <View style={styles.searchContainer}>
                    <Ionicons name="search" size={18} color={colors.textMuted} style={styles.searchIcon} />
                    <TextInput
                        style={styles.searchInput}
                        placeholder="Search channels..."
                        placeholderTextColor={colors.textMuted}
                        value={searchQuery}
                        onChangeText={setSearchQuery}
                    />
                    {searchQuery !== '' && (
                        <TouchableOpacity onPress={() => setSearchQuery('')} hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}>
                            <Ionicons name="close-circle" size={18} color={colors.textMuted} />
                        </TouchableOpacity>
                    )}
                </View>
            </View>

            {loading && forums.length === 0 ? (
                <View style={styles.center}><ActivityIndicator size="large" color={colors.foreground} /></View>
            ) : (
                <ScrollView style={styles.list} showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingBottom: insets.bottom + 24 }}>
                    {categorizedForums.map((category) => category.channels.length > 0 && (
                        <View key={category.key} style={styles.section}>
                            <View style={styles.sectionHeader}>
                                <View style={[styles.sectionAccent, category.key === 'OFFICIAL' && styles.sectionAccentOfficial]} />
                                <Text style={styles.sectionTitle}>{category.title}</Text>
                            </View>
                            {category.channels.map(channel => {
                                const isOfficial = category.key === 'OFFICIAL';
                                return (
                                    <TouchableOpacity
                                        key={channel.id}
                                        style={[styles.card, activeChannelId === channel.id && styles.cardActive]}
                                        onPress={() => handleChannelPress(channel)}
                                        activeOpacity={0.7}
                                    >
                                        <View style={[styles.iconWrap, isOfficial && styles.iconWrapOfficial]}>
                                            <Ionicons name="chatbubbles" size={20} color={isOfficial ? colors.info : colors.textSecondary} />
                                        </View>
                                        <View style={styles.info}>
                                            <Text style={styles.channelName} numberOfLines={1}>{channel.name}</Text>
                                            <Text style={styles.channelDesc} numberOfLines={2}>{channel.description || 'No description'}</Text>
                                        </View>
                                        <Ionicons name="chevron-forward" size={20} color={colors.textMuted} />
                                    </TouchableOpacity>
                                );
                            })}
                        </View>
                    ))}
                    {forums.length === 0 && (
                        <View style={styles.empty}>
                            <View style={styles.emptyIconWrap}>
                                <Ionicons name="chatbubbles-outline" size={48} color={colors.textMuted} />
                            </View>
                            <Text style={styles.emptyTitle}>No channels found</Text>
                            <Text style={styles.emptySubtitle}>{searchQuery ? 'Try a different search' : 'Channels will appear here'}</Text>
                        </View>
                    )}
                </ScrollView>
            )}
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    header: { paddingHorizontal: spacing.lg, paddingBottom: spacing.lg },
    headerTitle: { fontSize: 28, fontWeight: '700', color: colors.foreground, letterSpacing: -0.5 },
    headerSubtitle: { fontSize: 14, color: colors.textMuted, marginTop: 4, marginBottom: spacing.lg },
    searchContainer: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.card,
        borderRadius: 12,
        paddingHorizontal: spacing.md,
        height: 44,
        borderWidth: 1,
        borderColor: colors.border,
        ...shadows.sm,
    },
    searchIcon: { marginRight: spacing.sm },
    searchInput: { flex: 1, color: colors.textPrimary, fontSize: 15 },
    center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
    list: { flex: 1, paddingHorizontal: spacing.lg },
    section: { marginBottom: spacing.xl },
    sectionHeader: { flexDirection: 'row', alignItems: 'center', marginBottom: spacing.md },
    sectionAccent: { width: 4, height: 18, borderRadius: 2, backgroundColor: colors.foreground, marginRight: spacing.sm },
    sectionAccentOfficial: { backgroundColor: colors.info },
    sectionTitle: { fontSize: 13, fontWeight: '600', color: colors.textMuted, letterSpacing: 0.5 },
    card: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: colors.card,
        borderRadius: 14,
        padding: spacing.md,
        marginBottom: spacing.sm,
        borderWidth: 1,
        borderColor: 'transparent',
        ...shadows.sm,
    },
    cardActive: {
        borderColor: colors.foreground,
        ...shadows.md,
    },
    iconWrap: {
        width: 44,
        height: 44,
        borderRadius: 12,
        backgroundColor: colors.surface,
        justifyContent: 'center',
        alignItems: 'center',
        marginRight: spacing.md,
    },
    iconWrapOfficial: { backgroundColor: colors.accentMuted },
    info: { flex: 1, minWidth: 0 },
    channelName: { fontSize: 16, fontWeight: '600', color: colors.foreground },
    channelDesc: { fontSize: 13, color: colors.textMuted, marginTop: 2, lineHeight: 18 },
    empty: { alignItems: 'center', marginTop: 48 },
    emptyIconWrap: {
        width: 88,
        height: 88,
        borderRadius: 44,
        backgroundColor: colors.surface,
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: spacing.lg,
    },
    emptyTitle: { fontSize: 18, fontWeight: '600', color: colors.foreground, marginBottom: 4 },
    emptySubtitle: { fontSize: 14, color: colors.textMuted },
});
