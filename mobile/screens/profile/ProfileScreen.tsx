import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Image, Modal, TextInput, Alert, ActivityIndicator, Animated } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme/dark';

export default function ProfileScreen() {
    const navigation = useNavigation<any>();
    const { user, logout, refreshUser } = useAuth();
    const [scans, setScans] = useState<any[]>([]);
    const [myRank, setMyRank] = useState<any>(null);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [editBio, setEditBio] = useState('');
    const [editFirstName, setEditFirstName] = useState('');
    const [editLastName, setEditLastName] = useState('');
    const [editUsername, setEditUsername] = useState('');
    const [editAvatarUri, setEditAvatarUri] = useState<string | null>(null);
    const [saveLoading, setSaveLoading] = useState(false);
    const fadeAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        loadData();
        Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }).start();
    }, []);

    const loadData = async () => {
        try { const scanHistory = await api.getScanHistory().catch(() => ({ scans: [] })); setScans(scanHistory.scans || []); const rank = await api.getMyRank().catch(() => null); setMyRank(rank); } catch (e) { console.error(e); }
    };

    const handleEditPress = () => { 
        setEditBio(user?.profile?.bio || ''); 
        setEditFirstName(user?.first_name || ''); 
        setEditLastName(user?.last_name || ''); 
        setEditUsername(user?.username || ''); 
        setEditAvatarUri(null); 
        setEditModalVisible(true); 
    };
    const pickImage = async () => { const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: ImagePicker.MediaTypeOptions.Images, allowsEditing: true, aspect: [1, 1], quality: 0.8 }); if (!result.canceled) setEditAvatarUri(result.assets[0].uri); };

    const saveProfile = async () => {
        setSaveLoading(true);
        try {
            let newAvatarUrl = user?.profile?.avatar_url;
            if (editAvatarUri) { 
                try {
                    const res = await api.uploadAvatar(editAvatarUri); 
                    newAvatarUrl = res.avatar_url; 
                } catch (avatarError: any) {
                    console.error('Avatar upload error:', avatarError);
                    // Continue with profile update even if avatar fails
                }
            }
            
            // Update profile (bio, avatar)
            try {
                await api.updateProfile({ bio: editBio, avatar_url: newAvatarUrl });
                console.log('Profile updated successfully');
            } catch (profileError: any) {
                console.error('Profile update error:', profileError);
                throw profileError;
            }
            
            // Update account info (first_name, last_name, username)
            const accountUpdates: any = {};
            const currentFirstName = user?.first_name || '';
            const currentLastName = user?.last_name || '';
            const currentUsername = user?.username || '';
            
            // Always include fields that have changed or are being set for the first time
            if (editFirstName.trim() !== currentFirstName) {
                accountUpdates.first_name = editFirstName.trim() || null;
            }
            if (editLastName.trim() !== currentLastName) {
                accountUpdates.last_name = editLastName.trim() || null;
            }
            if (editUsername.trim() !== currentUsername) {
                const trimmedUsername = editUsername.trim();
                if (trimmedUsername) {
                    if (trimmedUsername.length < 3) {
                        Alert.alert('Error', 'Username must be at least 3 characters');
                        setSaveLoading(false);
                        return;
                    }
                    if (!/^[a-zA-Z0-9_]+$/.test(trimmedUsername)) {
                        Alert.alert('Error', 'Username can only contain letters, numbers, and underscores');
                        setSaveLoading(false);
                        return;
                    }
                }
                accountUpdates.username = trimmedUsername || null;
            }
            
            // Always call updateAccount if there are any changes
            if (Object.keys(accountUpdates).length > 0) {
                console.log('Updating account with:', accountUpdates);
                try {
                    await api.updateAccount(accountUpdates);
                    console.log('Account updated successfully');
                } catch (accountError: any) {
                    console.error('Account update error:', accountError);
                    throw accountError;
                }
            } else {
                console.log('No account fields to update');
            }
            
            // Refresh user data to get latest changes
            await refreshUser(); 
            setEditModalVisible(false); 
            Alert.alert('Success', 'Profile updated!');
        } catch (e: any) { 
            console.error('Save profile error:', e); 
            console.error('Error response:', e?.response);
            console.error('Error response data:', e?.response?.data);
            const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to update profile';
            Alert.alert('Error', errorMsg); 
        }
        finally { setSaveLoading(false); }
    };

    const safeNumber = (val: any, fallback: string = '-'): string => { const num = parseFloat(val); return isNaN(num) ? fallback : num.toFixed(1); };

    return (
        <View style={styles.container}>
            <View style={styles.topBar}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton} activeOpacity={0.7}>
                    <Ionicons name="arrow-back" size={20} color={colors.foreground} />
                </TouchableOpacity>
                <Text style={styles.topBarTitle}>Profile</Text>
                <View style={{ width: 40 }} />
            </View>

            <Animated.ScrollView showsVerticalScrollIndicator={false} style={{ opacity: fadeAnim }}>
                <View style={styles.header}>
                    <TouchableOpacity onPress={handleEditPress} style={styles.avatarContainer}>
                        {user?.profile?.avatar_url ? (
                            <Image source={{ uri: user.profile.avatar_url }} style={styles.avatarImage} />
                        ) : (
                            <View style={styles.avatarPlaceholder}><Ionicons name="person" size={40} color={colors.textMuted} /></View>
                        )}
                    </TouchableOpacity>
                    <Text style={styles.email}>{user?.first_name ? `${user.first_name} ${user.last_name || ''}`.trim() : user?.email}</Text>
                    {user?.username && <Text style={styles.username}>@{user.username}</Text>}
                    {user?.profile?.bio ? <Text style={styles.bio}>{user.profile.bio}</Text> : null}
                    <TouchableOpacity style={styles.editPill} onPress={handleEditPress} activeOpacity={0.7}>
                        <Text style={styles.editPillText}>Edit Profile</Text>
                    </TouchableOpacity>
                </View>

                <View style={styles.statsCard}>
                    <View style={styles.statItem}><Text style={styles.statValue}>{safeNumber(user?.profile?.current_level)}</Text><Text style={styles.statLabel}>Level</Text></View>
                    <View style={styles.statDivider} />
                    <View style={styles.statItem}><Text style={styles.statValue}>{myRank?.rank !== null ? `#${myRank?.rank}` : '-'}</Text><Text style={styles.statLabel}>Rank</Text></View>
                    <View style={styles.statDivider} />
                    <View style={styles.statItem}><Text style={styles.statValue}>{scans.length}</Text><Text style={styles.statLabel}>Scans</Text></View>
                </View>

                <View style={styles.sectionContainer}>
                    <Text style={styles.sectionLabel}>ACCOUNT SETTINGS</Text>
                    <View style={styles.settingsList}>
                        <TouchableOpacity
                            style={styles.settingsItem}
                            onPress={() => navigation.navigate('EditPersonal')}
                            activeOpacity={0.7}
                        >
                            <Ionicons name="person-outline" size={18} color={colors.textSecondary} />
                            <View style={styles.settingsInfo}><Text style={styles.settingsText}>Edit My Personal Info</Text></View>
                            <Ionicons name="chevron-forward" size={16} color={colors.textMuted} />
                        </TouchableOpacity>
                    </View>
                </View>

                <TouchableOpacity style={styles.logoutButton} onPress={logout} activeOpacity={0.7}>
                    <Text style={styles.logoutText}>Sign Out</Text>
                </TouchableOpacity>
                <View style={{ height: spacing.xxl }} />
            </Animated.ScrollView>

            <Modal animationType="fade" transparent visible={editModalVisible} onRequestClose={() => setEditModalVisible(false)}>
                <View style={styles.modalOverlay}>
                    <View style={styles.modalContent}>
                        <View style={styles.modalHeader}>
                            <Text style={styles.modalTitle}>Edit Profile</Text>
                            <TouchableOpacity onPress={() => setEditModalVisible(false)} style={styles.modalClose} activeOpacity={0.7}>
                                <Ionicons name="close" size={18} color={colors.textSecondary} />
                            </TouchableOpacity>
                        </View>
                        <TouchableOpacity onPress={pickImage} style={styles.modalAvatarContainer}>
                            {editAvatarUri ? <Image source={{ uri: editAvatarUri }} style={styles.modalAvatar} /> : user?.profile?.avatar_url ? <Image source={{ uri: user.profile.avatar_url }} style={styles.modalAvatar} /> : <View style={styles.modalAvatarPlaceholder}><Ionicons name="camera" size={28} color={colors.textMuted} /></View>}
                            <Text style={styles.changePhotoText}>Change Photo</Text>
                        </TouchableOpacity>
                        <Text style={styles.inputLabel}>FIRST NAME</Text>
                        <TextInput style={styles.input} value={editFirstName} onChangeText={setEditFirstName} placeholder="First name" placeholderTextColor={colors.textMuted} autoCapitalize="words" />
                        <Text style={styles.inputLabel}>LAST NAME</Text>
                        <TextInput style={styles.input} value={editLastName} onChangeText={setEditLastName} placeholder="Last name" placeholderTextColor={colors.textMuted} autoCapitalize="words" />
                        <Text style={styles.inputLabel}>USERNAME</Text>
                        <TextInput style={styles.input} value={editUsername} onChangeText={setEditUsername} placeholder="username" placeholderTextColor={colors.textMuted} autoCapitalize="none" />
                        <Text style={styles.inputLabel}>EMAIL (Cannot be changed)</Text>
                        <TextInput style={[styles.input, styles.inputDisabled]} value={user?.email || ''} editable={false} placeholderTextColor={colors.textMuted} />
                        <Text style={styles.inputLabel}>BIO</Text>
                        <TextInput style={styles.bioInput} value={editBio} onChangeText={setEditBio} multiline numberOfLines={3} placeholder="Tell us about yourself..." placeholderTextColor={colors.textMuted} />
                        <View style={styles.modalButtons}>
                            <TouchableOpacity style={styles.cancelButton} onPress={() => setEditModalVisible(false)}><Text style={styles.cancelButtonText}>Cancel</Text></TouchableOpacity>
                            <TouchableOpacity style={styles.saveButton} onPress={saveProfile} disabled={saveLoading} activeOpacity={0.7}>{saveLoading ? <ActivityIndicator color={colors.buttonText} /> : <Text style={styles.saveButtonText}>Save</Text>}</TouchableOpacity>
                        </View>
                    </View>
                </View>
            </Modal>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    topBar: {
        flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
        paddingTop: 56, paddingHorizontal: spacing.lg, paddingBottom: spacing.sm,
    },
    backButton: { width: 36, height: 36, borderRadius: 18, backgroundColor: colors.card, alignItems: 'center', justifyContent: 'center', ...shadows.sm },
    topBarTitle: { fontSize: 15, fontWeight: '600', color: colors.foreground },
    header: { alignItems: 'center', paddingTop: spacing.lg, paddingBottom: spacing.xl },
    avatarContainer: { position: 'relative' },
    avatarImage: { width: 88, height: 88, borderRadius: 44, ...shadows.md },
    avatarPlaceholder: { width: 88, height: 88, borderRadius: 44, backgroundColor: colors.surface, justifyContent: 'center', alignItems: 'center', ...shadows.sm },
    email: { fontSize: 15, fontWeight: '600', color: colors.foreground, marginTop: spacing.md },
    username: { fontSize: 13, color: colors.textMuted, marginTop: 2 },
    bio: { fontSize: 13, color: colors.textSecondary, marginTop: 4, textAlign: 'center', paddingHorizontal: spacing.xxl },
    editPill: { marginTop: spacing.md, paddingHorizontal: spacing.lg, paddingVertical: 8, borderRadius: borderRadius.full, backgroundColor: colors.card, ...shadows.sm },
    editPillText: { fontSize: 12, fontWeight: '500', color: colors.textSecondary },
    statsCard: {
        flexDirection: 'row', marginHorizontal: spacing.lg,
        backgroundColor: colors.card, borderRadius: borderRadius['2xl'],
        padding: spacing.lg, ...shadows.md,
    },
    statItem: { flex: 1, alignItems: 'center' },
    statValue: { fontSize: 24, fontWeight: '600', color: colors.foreground },
    statLabel: { ...typography.caption, marginTop: 4 },
    statDivider: { width: 1, backgroundColor: colors.borderLight },
    sectionContainer: { paddingHorizontal: spacing.lg, marginTop: spacing.xl },
    sectionLabel: { ...typography.label, marginBottom: spacing.md },
    scanList: {
        backgroundColor: colors.card, borderRadius: borderRadius['2xl'],
        padding: spacing.md, ...shadows.sm,
    },
    scanItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.borderLight },
    scanInfo: { flex: 1, marginLeft: spacing.md },
    scanDate: { fontSize: 13, color: colors.textSecondary },
    scanScore: { fontSize: 16, fontWeight: '600', color: colors.foreground, marginRight: spacing.sm },
    emptyText: { fontSize: 13, color: colors.textMuted, textAlign: 'center', padding: spacing.lg },
    logoutButton: { alignItems: 'center', marginTop: spacing.xl, padding: spacing.md },
    logoutText: { fontSize: 14, fontWeight: '500', color: colors.error },
    settingsList: {
        backgroundColor: colors.card, borderRadius: borderRadius['2xl'],
        padding: spacing.md, ...shadows.sm,
    },
    settingsItem: { flexDirection: 'row', alignItems: 'center', paddingVertical: spacing.md },
    settingsInfo: { flex: 1, marginLeft: spacing.md },
    settingsText: { fontSize: 14, color: colors.foreground, fontWeight: '500' },
    modalOverlay: { flex: 1, backgroundColor: colors.overlay, justifyContent: 'center', padding: spacing.lg },
    modalContent: {
        backgroundColor: colors.card, borderRadius: borderRadius['2xl'],
        padding: spacing.xl, ...shadows.xl,
    },
    modalHeader: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.lg },
    modalTitle: { ...typography.h3 },
    modalClose: { width: 32, height: 32, borderRadius: 16, backgroundColor: colors.surface, alignItems: 'center', justifyContent: 'center' },
    modalAvatarContainer: { alignSelf: 'center', alignItems: 'center', marginBottom: spacing.lg },
    modalAvatar: { width: 72, height: 72, borderRadius: 36 },
    modalAvatarPlaceholder: { width: 72, height: 72, borderRadius: 36, backgroundColor: colors.surface, justifyContent: 'center', alignItems: 'center' },
    changePhotoText: { fontSize: 12, color: colors.info, fontWeight: '500', marginTop: spacing.sm },
    inputLabel: { ...typography.label, marginBottom: spacing.xs, marginLeft: 2 },
    input: {
        backgroundColor: colors.surface, borderRadius: borderRadius.md, padding: spacing.md,
        color: colors.textPrimary, fontSize: 14, marginBottom: spacing.md,
    },
    inputDisabled: {
        opacity: 0.6, backgroundColor: colors.card,
    },
    bioInput: { backgroundColor: colors.surface, borderRadius: borderRadius.md, padding: spacing.md, color: colors.textPrimary, fontSize: 14, textAlignVertical: 'top', minHeight: 80 },
    modalButtons: { flexDirection: 'row', justifyContent: 'flex-end', marginTop: spacing.lg, gap: spacing.md },
    cancelButton: { padding: spacing.md },
    cancelButtonText: { fontSize: 14, fontWeight: '500', color: colors.textMuted },
    saveButton: { backgroundColor: colors.foreground, borderRadius: borderRadius.full, paddingHorizontal: spacing.xl, paddingVertical: spacing.md, ...shadows.sm },
    saveButtonText: { ...typography.button },
});
