import React, { useState, useEffect, useRef } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert, Animated, TextInput, KeyboardAvoidingView, Platform } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme/dark';

const GOALS = [
    { id: 'jawline', label: 'Jawline', icon: 'fitness' },
    { id: 'fat_loss', label: 'Fat Loss', icon: 'body' },
    { id: 'skin', label: 'Skin', icon: 'sparkles' },
    { id: 'posture', label: 'Posture', icon: 'walk' },
    { id: 'symmetry', label: 'Symmetry', icon: 'grid' },
    { id: 'hair', label: 'Hair', icon: 'cut' },
];

const EXPERIENCE = [
    { id: 'beginner', label: 'Beginner', desc: 'Just getting started' },
    { id: 'intermediate', label: 'Intermediate', desc: 'Some experience' },
    { id: 'advanced', label: 'Advanced', desc: 'Experienced practitioner' },
];

const ACTIVITY_LEVELS = [
    { id: 'sedentary', label: 'Sedentary', desc: 'Little to no exercise' },
    { id: 'light', label: 'Light', desc: '1-3 days/week' },
    { id: 'moderate', label: 'Moderate', desc: '3-5 days/week' },
    { id: 'active', label: 'Active', desc: '6-7 days/week' },
];

const EQUIPMENT = [
    { id: 'none', label: 'None / Bodyweight', icon: 'hand-left' },
    { id: 'dumbbells', label: 'Dumbbells', icon: 'barbell' },
    { id: 'gym', label: 'Full Gym Access', icon: 'business' },
];

const SKIN_TYPES = [
    { id: 'oily', label: 'Oily' },
    { id: 'dry', label: 'Dry' },
    { id: 'combination', label: 'Combination' },
    { id: 'sensitive', label: 'Sensitive' },
];

export default function OnboardingScreen() {
    const navigation = useNavigation<any>();
    const { user, refreshUser } = useAuth();

    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);

    // Form State
    const [selectedGoals, setSelectedGoals] = useState<string[]>([]);
    const [gender, setGender] = useState('');
    const [age, setAge] = useState('');
    const [unitSystem, setUnitSystem] = useState<'metric' | 'imperial'>('metric');

    const [height, setHeight] = useState('');
    const [heightFt, setHeightFt] = useState('');
    const [heightIn, setHeightIn] = useState('');
    const [weight, setWeight] = useState('');
    const [activityLevel, setActivityLevel] = useState('');
    const [selectedEquipment, setSelectedEquipment] = useState<string[]>([]);
    const [experience, setExperience] = useState('');
    const [skinType, setSkinType] = useState('');

    const fadeAnim = useRef(new Animated.Value(0)).current;

    useEffect(() => {
        Animated.timing(fadeAnim, { toValue: 1, duration: 400, useNativeDriver: true }).start();
    }, [step]);

    const nextStep = () => {
        if (step === 1 && selectedGoals.length === 0) { Alert.alert('Required', 'Please select at least one goal'); return; }
        if (step === 2) {
            if (!gender || !age || !weight) { Alert.alert('Required', 'Please fill in all physical profile fields'); return; }
            if (unitSystem === 'metric' && !height) { Alert.alert('Required', 'Please fill in all physical profile fields'); return; }
            if (unitSystem === 'imperial' && (!heightFt || !heightIn)) { Alert.alert('Required', 'Please fill in all physical profile fields'); return; }
        }
        if (step === 3 && (!activityLevel || selectedEquipment.length === 0)) { Alert.alert('Required', 'Please select activity level and equipment'); return; }

        if (step < 4) {
            Animated.timing(fadeAnim, { toValue: 0, duration: 200, useNativeDriver: true }).start(() => {
                setStep(step + 1);
            });
        } else {
            handleFinish();
        }
    };

    const prevStep = () => {
        if (step > 1) {
            Animated.timing(fadeAnim, { toValue: 0, duration: 200, useNativeDriver: true }).start(() => {
                setStep(step - 1);
            });
        }
    };

    const handleFinish = async () => {
        if (!experience || !skinType) { Alert.alert('Required', 'Please complete the final step'); return; }
        setLoading(true);

        let finalHeight = parseFloat(height);
        let finalWeight = parseFloat(weight);

        // Convert to metric for backend storage consistent with other users
        if (unitSystem === 'imperial') {
            const ft = parseInt(heightFt) || 0;
            const inch = parseInt(heightIn) || 0;
            finalHeight = (ft * 30.48) + (inch * 2.54);
            finalWeight = parseFloat(weight) * 0.453592;
        }

        try {
            await api.saveOnboarding({
                goals: selectedGoals,
                gender,
                age: parseInt(age),
                height: Math.round(finalHeight * 10) / 10,
                weight: Math.round(finalWeight * 10) / 10,
                activity_level: activityLevel,
                equipment: selectedEquipment,
                experience_level: experience,
                skin_type: skinType,
                unit_system: unitSystem,
                timezone: typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'UTC',
                completed: true
            });
            await refreshUser();
            navigation.navigate('FeaturesIntro');
        } catch (error) {
            Alert.alert('Error', 'Could not save your profile. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const renderStepContent = () => {
        switch (step) {
            case 1:
                return (
                    <View>
                        <Text style={styles.title}>What are your goals?</Text>
                        <Text style={styles.subtitle}>Select all the areas you want to optimize</Text>
                        <View style={styles.goalsGrid}>
                            {GOALS.map((goal) => {
                                const selected = selectedGoals.includes(goal.id);
                                return (
                                    <TouchableOpacity
                                        key={goal.id}
                                        style={[styles.goalCard, selected && styles.goalCardSelected]}
                                        onPress={() => setSelectedGoals(prev => prev.includes(goal.id) ? prev.filter(g => g !== goal.id) : [...prev, goal.id])}
                                    >
                                        <Ionicons name={goal.icon as any} size={24} color={selected ? colors.foreground : colors.textMuted} />
                                        <Text style={[styles.goalLabel, selected && styles.goalLabelSelected]}>{goal.label}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </View>
                    </View>
                );
            case 2:
                return (
                    <View>
                        <View style={styles.titleRow}>
                            <Text style={styles.title}>Physical Profile</Text>
                            <View style={styles.unitToggle}>
                                <TouchableOpacity
                                    onPress={() => setUnitSystem('metric')}
                                    style={[styles.unitBtn, unitSystem === 'metric' && styles.unitBtnActive]}
                                >
                                    <Text style={[styles.unitLabel, unitSystem === 'metric' && styles.unitLabelActive]}>Metric</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    onPress={() => setUnitSystem('imperial')}
                                    style={[styles.unitBtn, unitSystem === 'imperial' && styles.unitBtnActive]}
                                >
                                    <Text style={[styles.unitLabel, unitSystem === 'imperial' && styles.unitLabelActive]}>US</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                        <Text style={styles.subtitle}>Help Max understand your baseline</Text>

                        <Text style={styles.inputLabel}>GENDER</Text>
                        <View style={styles.row}>
                            {['Male', 'Female', 'Other'].map(g => (
                                <TouchableOpacity
                                    key={g}
                                    style={[styles.chip, gender === g && styles.chipSelected]}
                                    onPress={() => setGender(g)}
                                >
                                    <Text style={[styles.chipText, gender === g && styles.chipTextSelected]}>{g}</Text>
                                </TouchableOpacity>
                            ))}
                        </View>

                        <View style={styles.inputGroup}>
                            <View style={styles.inputHalf}>
                                <Text style={styles.inputLabel}>AGE</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder="Years"
                                    placeholderTextColor={colors.textMuted}
                                    keyboardType="numeric"
                                    value={age}
                                    onChangeText={setAge}
                                />
                            </View>
                            <View style={styles.inputHalf}>
                                <Text style={styles.inputLabel}>WEIGHT ({unitSystem === 'metric' ? 'KG' : 'LBS'})</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder={unitSystem === 'metric' ? "kg" : "lbs"}
                                    placeholderTextColor={colors.textMuted}
                                    keyboardType="numeric"
                                    value={weight}
                                    onChangeText={setWeight}
                                />
                            </View>
                        </View>

                        <Text style={styles.inputLabel}>HEIGHT ({unitSystem === 'metric' ? 'CM' : 'FT/IN'})</Text>
                        {unitSystem === 'metric' ? (
                            <TextInput
                                style={styles.input}
                                placeholder="cm"
                                placeholderTextColor={colors.textMuted}
                                keyboardType="numeric"
                                value={height}
                                onChangeText={setHeight}
                            />
                        ) : (
                            <View style={styles.inputGroup}>
                                <View style={styles.inputHalf}>
                                    <TextInput
                                        style={styles.input}
                                        placeholder="ft"
                                        placeholderTextColor={colors.textMuted}
                                        keyboardType="numeric"
                                        value={heightFt}
                                        onChangeText={setHeightFt}
                                    />
                                </View>
                                <View style={styles.inputHalf}>
                                    <TextInput
                                        style={styles.input}
                                        placeholder="in"
                                        placeholderTextColor={colors.textMuted}
                                        keyboardType="numeric"
                                        value={heightIn}
                                        onChangeText={setHeightIn}
                                    />
                                </View>
                            </View>
                        )}
                    </View>
                );
            case 3:
                return (
                    <View>
                        <Text style={styles.title}>Lifestyle</Text>
                        <Text style={styles.subtitle}>Let&apos;s talk about your routine</Text>

                        <Text style={styles.inputLabel}>ACTIVITY LEVEL</Text>
                        <View style={styles.list}>
                            {ACTIVITY_LEVELS.map(level => (
                                <TouchableOpacity
                                    key={level.id}
                                    style={[styles.listCard, activityLevel === level.id && styles.listCardSelected]}
                                    onPress={() => setActivityLevel(level.id)}
                                >
                                    <View>
                                        <Text style={styles.listLabel}>{level.label}</Text>
                                        <Text style={styles.listDesc}>{level.desc}</Text>
                                    </View>
                                </TouchableOpacity>
                            ))}
                        </View>

                        <Text style={[styles.inputLabel, { marginTop: spacing.lg }]}>EQUIPMENT ACCESS</Text>
                        <View style={styles.row}>
                            {EQUIPMENT.map(item => {
                                const selected = selectedEquipment.includes(item.id);
                                return (
                                    <TouchableOpacity
                                        key={item.id}
                                        style={[styles.goalCard, { width: '31%' }, selected && styles.goalCardSelected]}
                                        onPress={() => setSelectedEquipment(prev => prev.includes(item.id) ? prev.filter(i => i !== item.id) : [...prev, item.id])}
                                    >
                                        <Ionicons name={item.icon as any} size={20} color={selected ? colors.foreground : colors.textMuted} />
                                        <Text style={styles.caption}>{item.label}</Text>
                                    </TouchableOpacity>
                                );
                            })}
                        </View>
                    </View>
                );
            case 4:
                return (
                    <View>
                        <Text style={styles.title}>Last Details</Text>
                        <Text style={styles.subtitle}>Finalize your personalized profile</Text>

                        <Text style={styles.inputLabel}>EXPERIENCE LEVEL</Text>
                        <View style={styles.list}>
                            {EXPERIENCE.map(exp => (
                                <TouchableOpacity
                                    key={exp.id}
                                    style={[styles.listCard, experience === exp.id && styles.listCardSelected]}
                                    onPress={() => setExperience(exp.id)}
                                >
                                    <View>
                                        <Text style={styles.listLabel}>{exp.label}</Text>
                                        <Text style={styles.listDesc}>{exp.desc}</Text>
                                    </View>
                                </TouchableOpacity>
                            ))}
                        </View>

                        <Text style={[styles.inputLabel, { marginTop: spacing.lg }]}>SKIN TYPE</Text>
                        <View style={styles.flexRow}>
                            {SKIN_TYPES.map(type => (
                                <TouchableOpacity
                                    key={type.id}
                                    style={[styles.chip, skinType === type.id && styles.chipSelected]}
                                    onPress={() => setSkinType(type.id)}
                                >
                                    <Text style={[styles.chipText, skinType === type.id && styles.chipTextSelected]}>{type.label}</Text>
                                </TouchableOpacity>
                            ))}
                        </View>
                    </View>
                );
        }
    };

    return (
        <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
            <ScrollView style={styles.container} contentContainerStyle={styles.content}>
                <View style={styles.header}>
                    <TouchableOpacity onPress={prevStep} disabled={step === 1} style={{ opacity: step === 1 ? 0 : 1 }}>
                        <Ionicons name="arrow-back" size={24} color={colors.foreground} />
                    </TouchableOpacity>
                    <Text style={styles.stepIndicator}>Step {step} of 4</Text>
                    <View style={{ width: 24 }} />
                </View>

                <View style={styles.progressBar}>
                    <View style={[styles.progressIndicator, { width: `${(step / 4) * 100}%` }]} />
                </View>

                <Animated.View style={{ opacity: fadeAnim }}>
                    {renderStepContent()}
                </Animated.View>

                <TouchableOpacity
                    style={[styles.button, { marginTop: spacing.xl }, loading && { opacity: 0.7 }]}
                    onPress={nextStep}
                    disabled={loading}
                >
                    <Text style={styles.buttonText}>{loading ? 'Finalizing...' : step === 4 ? 'Complete Profile' : 'Continue'}</Text>
                </TouchableOpacity>
            </ScrollView>
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    content: { padding: spacing.lg, paddingTop: 60, paddingBottom: 40 },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.md },
    stepIndicator: { ...typography.label, color: colors.textMuted },
    progressBar: { height: 4, backgroundColor: colors.card, borderRadius: 2, marginBottom: 40 },
    progressIndicator: { height: '100%', backgroundColor: colors.foreground, borderRadius: 2 },
    title: { ...typography.h1, marginBottom: spacing.xs },
    titleRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: spacing.xs },
    unitToggle: {
        flexDirection: 'row',
        backgroundColor: colors.card,
        borderRadius: borderRadius.full,
        padding: 4,
        borderWidth: 1,
        borderColor: colors.borderLight,
    },
    unitBtn: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: borderRadius.full,
    },
    unitBtnActive: {
        backgroundColor: colors.foreground,
    },
    unitLabel: {
        fontSize: 12,
        fontWeight: '600',
        color: colors.textMuted,
    },
    unitLabelActive: {
        color: colors.background,
    },
    subtitle: { ...typography.bodySmall, color: colors.textSecondary, marginBottom: 40 },
    goalsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
    goalCard: {
        width: '31%',
        backgroundColor: colors.card,
        borderRadius: borderRadius.lg,
        padding: spacing.md,
        alignItems: 'center',
        justifyContent: 'center',
        borderWidth: 1,
        borderColor: 'transparent',
        ...shadows.sm,
    },
    goalCardSelected: { backgroundColor: colors.accentMuted, borderColor: colors.foreground },
    goalLabel: { ...typography.caption, marginTop: spacing.xs, color: colors.textSecondary, textAlign: 'center' },
    goalLabelSelected: { color: colors.foreground, fontWeight: '600' },
    inputLabel: { ...typography.label, color: colors.textMuted, marginBottom: spacing.sm, marginTop: spacing.md },
    row: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
    flexRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
    chip: {
        paddingHorizontal: 20,
        paddingVertical: 10,
        borderRadius: borderRadius.full,
        backgroundColor: colors.card,
        borderWidth: 1,
        borderColor: colors.borderLight,
    },
    chipSelected: { backgroundColor: colors.foreground, borderColor: colors.foreground },
    chipText: { ...typography.bodySmall, color: colors.textSecondary },
    chipTextSelected: { color: colors.background, fontWeight: '600' },
    inputGroup: { flexDirection: 'row', gap: spacing.md },
    inputHalf: { flex: 1 },
    input: {
        backgroundColor: colors.card,
        borderRadius: borderRadius.md,
        padding: 16,
        color: colors.foreground,
        fontSize: 16,
        borderWidth: 1,
        borderColor: colors.borderLight,
    },
    list: { gap: spacing.sm },
    listCard: {
        backgroundColor: colors.card,
        borderRadius: borderRadius.lg,
        padding: 16,
        borderWidth: 1,
        borderColor: 'transparent',
    },
    listCardSelected: { backgroundColor: colors.accentMuted, borderColor: colors.foreground },
    listLabel: { ...typography.body, fontWeight: '600', color: colors.foreground },
    listDesc: { ...typography.caption, color: colors.textMuted, marginTop: 2 },
    button: {
        backgroundColor: colors.foreground,
        borderRadius: borderRadius.full,
        paddingVertical: 18,
        alignItems: 'center',
        ...shadows.md,
    },
    buttonText: { ...typography.button, color: colors.background },
    caption: { ...typography.caption, color: colors.textMuted, textAlign: 'center', marginTop: 4 },
});
