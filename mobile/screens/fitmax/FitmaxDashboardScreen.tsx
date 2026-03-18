import React, { useEffect, useMemo, useState } from 'react';
import {
    ActivityIndicator,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import { colors, spacing, borderRadius, typography, shadows } from '../../theme/dark';

type TabKey = 'plan' | 'tracker' | 'nutrition' | 'progress' | 'course';

const GOAL_OPTIONS = [
    { id: 'lose_weight_cut', label: 'Lose Weight / Cut' },
    { id: 'gain_muscle_bulk', label: 'Gain Muscle / Bulk' },
    { id: 'body_recomposition', label: 'Body Recomposition' },
    { id: 'maintain_tone', label: 'Maintain & Tone' },
    { id: 'athletic_performance', label: 'Athletic Performance' },
];

const ACCESS_OPTIONS = [
    { id: 'full_gym', label: 'Full Gym' },
    { id: 'dumbbells_only', label: 'Dumbbells Only' },
    { id: 'bodyweight_only', label: 'Bodyweight Only' },
    { id: 'resistance_bands', label: 'Resistance Bands' },
    { id: 'mixed_varies', label: 'Mixed / Varies' },
];

const ACTIVITY_OPTIONS = [
    { id: 'sedentary', label: 'Sedentary' },
    { id: 'lightly_active', label: 'Lightly Active' },
    { id: 'moderately_active', label: 'Moderately Active' },
    { id: 'very_active', label: 'Very Active' },
];

const CAL_TRACK_OPTIONS = [
    { id: 'yes', label: 'Tracking Calories' },
    { id: 'no', label: 'Not Tracking' },
    { id: 'want_to_start', label: 'Want to Start' },
];

const EATING_GOAL_OPTIONS = [
    { id: 'eat_more', label: 'Eat More' },
    { id: 'eat_less', label: 'Eat Less' },
    { id: 'eat_better', label: 'Eat Better' },
    { id: 'unsure', label: 'Unsure' },
];

const TIME_PREF_OPTIONS = [
    { id: 'morning', label: 'Morning' },
    { id: 'afternoon', label: 'Afternoon' },
    { id: 'evening', label: 'Evening' },
];

const SESSION_LENGTHS = [30, 45, 60, 90];

const TABS: { key: TabKey; label: string }[] = [
    { key: 'plan', label: 'Workout Plan' },
    { key: 'tracker', label: 'Live Tracker' },
    { key: 'nutrition', label: 'Calories' },
    { key: 'progress', label: 'Progress' },
    { key: 'course', label: 'Course' },
];

function Pill({
    label,
    selected,
    onPress,
}: {
    label: string;
    selected: boolean;
    onPress: () => void;
}) {
    return (
        <TouchableOpacity
            style={[styles.pill, selected && styles.pillSelected]}
            onPress={onPress}
            activeOpacity={0.8}
        >
            <Text style={[styles.pillText, selected && styles.pillTextSelected]}>{label}</Text>
        </TouchableOpacity>
    );
}

export default function FitmaxDashboardScreen() {
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [tab, setTab] = useState<TabKey>('plan');

    const [profile, setProfile] = useState<any>(null);
    const [dashboard, setDashboard] = useState<any>(null);
    const [modules, setModules] = useState<any[]>([]);
    const [nutritionDay, setNutritionDay] = useState<any>(null);
    const [progress, setProgress] = useState<any>(null);

    const [goalType, setGoalType] = useState('gain_muscle_bulk');
    const [trainingAccess, setTrainingAccess] = useState<string[]>(['full_gym']);
    const [heightCm, setHeightCm] = useState('178');
    const [weightKg, setWeightKg] = useState('75');
    const [age, setAge] = useState('24');
    const [sex, setSex] = useState<'male' | 'female' | 'other'>('male');
    const [bodyFat, setBodyFat] = useState('');
    const [weeklyDays, setWeeklyDays] = useState('4');
    const [sessionLength, setSessionLength] = useState(45);
    const [timePref, setTimePref] = useState('evening');
    const [activityLevel, setActivityLevel] = useState('moderately_active');
    const [calTracking, setCalTracking] = useState('no');
    const [eatingGoal, setEatingGoal] = useState('unsure');
    const [dietaryRestrictions, setDietaryRestrictions] = useState('');

    const [selectedSessionIdx, setSelectedSessionIdx] = useState(0);
    const [startedAt, setStartedAt] = useState<Date | null>(null);
    const [exerciseLogs, setExerciseLogs] = useState<Record<string, { reps: string; weight: string }>>({});
    const [mealName, setMealName] = useState('');
    const [mealType, setMealType] = useState<'breakfast' | 'lunch' | 'dinner' | 'snacks'>('dinner');
    const [mealCalories, setMealCalories] = useState('');
    const [mealProtein, setMealProtein] = useState('');
    const [mealCarbs, setMealCarbs] = useState('');
    const [mealFats, setMealFats] = useState('');
    const [measurementWeight, setMeasurementWeight] = useState('');
    const [measurementWaist, setMeasurementWaist] = useState('');
    const [measurementChest, setMeasurementChest] = useState('');

    useEffect(() => {
        loadAll();
    }, []);

    const hydrateProfileForm = (p: any) => {
        if (!p) return;
        setGoalType(p.goal_type || 'gain_muscle_bulk');
        setTrainingAccess(p.training_access || ['full_gym']);
        setHeightCm(String(p.height_cm ?? ''));
        setWeightKg(String(p.weight_kg ?? ''));
        setAge(String(p.age ?? ''));
        setSex((p.biological_sex || 'male') as any);
        setBodyFat(p.body_fat_percent ? String(p.body_fat_percent) : '');
        setWeeklyDays(String(p.weekly_training_days ?? '4'));
        setSessionLength(Number(p.preferred_session_length || 45));
        setTimePref(p.preferred_time_of_day || 'evening');
        setActivityLevel(p.activity_level || 'moderately_active');
        setCalTracking(p.calorie_tracking || 'no');
        setEatingGoal(p.eating_goal || 'unsure');
        setDietaryRestrictions((p.dietary_restrictions || []).join(', '));
    };

    const loadAll = async () => {
        setLoading(true);
        try {
            const dash = await api.getFitmaxDashboard();
            setDashboard(dash);
            setProfile(dash?.profile || null);
            hydrateProfileForm(dash?.profile?.profile || null);
            const [modsRes, dayRes, progRes] = await Promise.all([
                api.getFitmaxCourseModules(),
                api.getFitmaxNutritionDay(),
                api.getFitmaxProgressOverview(),
            ]);
            setModules(modsRes?.modules || []);
            setNutritionDay(dayRes || null);
            setProgress(progRes || null);
        } catch (e: any) {
            if (e?.response?.status === 404) {
                setProfile(null);
                setDashboard(null);
            } else {
                console.error('Fitmax load failed', e?.response?.data || e?.message || e);
            }
        } finally {
            setLoading(false);
        }
    };

    const targets = dashboard?.profile?.targets || profile?.targets || {};
    const planSessions = dashboard?.plan_preview?.sessions || [];
    const trainingSessions = planSessions.filter((s: any) => s.is_training_day);
    const selectedSession = trainingSessions[selectedSessionIdx] || null;

    const saveProfile = async () => {
        setSaving(true);
        try {
            const payload = {
                goal_type: goalType,
                height_cm: Number(heightCm),
                weight_kg: Number(weightKg),
                age: Number(age),
                biological_sex: sex,
                body_fat_percent: bodyFat ? Number(bodyFat) : null,
                training_access: trainingAccess,
                weekly_training_days: Number(weeklyDays),
                preferred_session_length: Number(sessionLength),
                preferred_time_of_day: timePref,
                activity_level: activityLevel,
                dietary_restrictions: dietaryRestrictions
                    .split(',')
                    .map((x) => x.trim())
                    .filter(Boolean),
                calorie_tracking: calTracking,
                eating_goal: eatingGoal,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
            };
            await api.saveFitmaxProfile(payload);
            await api.refreshFitmaxCoachSchedule();
            await loadAll();
        } catch (e) {
            console.error('Fitmax save failed', e);
        } finally {
            setSaving(false);
        }
    };

    const completeWorkout = async () => {
        if (!selectedSession || !startedAt) return;
        const completedAt = new Date();
        const sets = (selectedSession.exercises || []).map((ex: any, idx: number) => {
            const key = `${ex.exercise_id}-${idx}`;
            const entry = exerciseLogs[key] || { reps: '0', weight: '0' };
            return {
                exercise_id: ex.exercise_id,
                set_index: 1,
                reps_completed: Number(entry.reps || 0),
                weight_kg: Number(entry.weight || 0),
            };
        });
        const totalVolume = sets.reduce((sum: number, s: any) => sum + (Number(s.weight_kg || 0) * Number(s.reps_completed || 0)), 0);
        try {
            await api.logFitmaxWorkout({
                started_at: startedAt.toISOString(),
                completed_at: completedAt.toISOString(),
                day_label: selectedSession.day_label,
                focus: selectedSession.focus,
                week_number: dashboard?.current_week || 1,
                sets,
                total_volume_kg: totalVolume,
            });
            setStartedAt(null);
            setExerciseLogs({});
            await loadAll();
        } catch (e) {
            console.error('Workout log failed', e);
        }
    };

    const logMeal = async () => {
        try {
            await api.logFitmaxNutrition({
                meal_name: mealName || 'Meal',
                meal_type: mealType,
                calories: Number(mealCalories || 0),
                protein_g: Number(mealProtein || 0),
                carbs_g: Number(mealCarbs || 0),
                fats_g: Number(mealFats || 0),
                food_items: mealName ? [mealName] : [],
            });
            setMealName('');
            setMealCalories('');
            setMealProtein('');
            setMealCarbs('');
            setMealFats('');
            const day = await api.getFitmaxNutritionDay();
            setNutritionDay(day);
            await loadAll();
        } catch (e) {
            console.error('Nutrition log failed', e);
        }
    };

    const logMeasurement = async () => {
        try {
            await api.logFitmaxMeasurements({
                weight_kg: measurementWeight ? Number(measurementWeight) : undefined,
                waist_cm: measurementWaist ? Number(measurementWaist) : undefined,
                chest_cm: measurementChest ? Number(measurementChest) : undefined,
            });
            setMeasurementWeight('');
            setMeasurementWaist('');
            setMeasurementChest('');
            const prog = await api.getFitmaxProgressOverview();
            setProgress(prog);
        } catch (e) {
            console.error('Measurement log failed', e);
        }
    };

    const weeklyStats = useMemo(() => {
        const ws = dashboard?.weekly_summary || {};
        const done = ws.workouts_completed || 0;
        const target = ws.workouts_target || 0;
        const pct = target ? Math.min(1, done / target) : 0;
        return { done, target, pct };
    }, [dashboard]);

    if (loading) {
        return (
            <View style={[styles.container, styles.center]}>
                <ActivityIndicator size="large" color={colors.foreground} />
            </View>
        );
    }

    if (!profile) {
        return (
            <ScrollView style={styles.container} contentContainerStyle={styles.content}>
                <Text style={styles.screenTitle}>Fitmax Setup</Text>
                <Text style={styles.subtitle}>This powers your workouts, calories, and coach texts.</Text>

                <Text style={styles.label}>Goal Type</Text>
                <View style={styles.pillRow}>
                    {GOAL_OPTIONS.map((o) => (
                        <Pill key={o.id} label={o.label} selected={goalType === o.id} onPress={() => setGoalType(o.id)} />
                    ))}
                </View>

                <Text style={styles.label}>Body Stats</Text>
                <View style={styles.row}>
                    <TextInput style={[styles.input, styles.half]} value={heightCm} onChangeText={setHeightCm} placeholder="Height cm" placeholderTextColor={colors.textMuted} keyboardType="decimal-pad" />
                    <TextInput style={[styles.input, styles.half]} value={weightKg} onChangeText={setWeightKg} placeholder="Weight kg" placeholderTextColor={colors.textMuted} keyboardType="decimal-pad" />
                </View>
                <View style={styles.row}>
                    <TextInput style={[styles.input, styles.half]} value={age} onChangeText={setAge} placeholder="Age" placeholderTextColor={colors.textMuted} keyboardType="number-pad" />
                    <TextInput style={[styles.input, styles.half]} value={bodyFat} onChangeText={setBodyFat} placeholder="Body fat % (optional)" placeholderTextColor={colors.textMuted} keyboardType="decimal-pad" />
                </View>
                <View style={styles.pillRow}>
                    {['male', 'female', 'other'].map((s) => (
                        <Pill key={s} label={s} selected={sex === s} onPress={() => setSex(s as any)} />
                    ))}
                </View>

                <Text style={styles.label}>Training Access</Text>
                <View style={styles.pillRow}>
                    {ACCESS_OPTIONS.map((o) => (
                        <Pill
                            key={o.id}
                            label={o.label}
                            selected={trainingAccess.includes(o.id)}
                            onPress={() =>
                                setTrainingAccess((prev) =>
                                    prev.includes(o.id) ? prev.filter((x) => x !== o.id) : [...prev, o.id]
                                )
                            }
                        />
                    ))}
                </View>

                <Text style={styles.label}>Weekly Availability</Text>
                <View style={styles.row}>
                    <TextInput style={[styles.input, styles.half]} value={weeklyDays} onChangeText={setWeeklyDays} placeholder="Days / week (2-6)" placeholderTextColor={colors.textMuted} keyboardType="number-pad" />
                    <View style={[styles.half, { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs }]}>
                        {SESSION_LENGTHS.map((n) => (
                            <Pill key={n} label={`${n}m`} selected={sessionLength === n} onPress={() => setSessionLength(n)} />
                        ))}
                    </View>
                </View>
                <View style={styles.pillRow}>
                    {TIME_PREF_OPTIONS.map((o) => (
                        <Pill key={o.id} label={o.label} selected={timePref === o.id} onPress={() => setTimePref(o.id)} />
                    ))}
                </View>

                <Text style={styles.label}>Activity + Diet Context</Text>
                <View style={styles.pillRow}>
                    {ACTIVITY_OPTIONS.map((o) => (
                        <Pill key={o.id} label={o.label} selected={activityLevel === o.id} onPress={() => setActivityLevel(o.id)} />
                    ))}
                </View>
                <View style={styles.pillRow}>
                    {CAL_TRACK_OPTIONS.map((o) => (
                        <Pill key={o.id} label={o.label} selected={calTracking === o.id} onPress={() => setCalTracking(o.id)} />
                    ))}
                </View>
                <View style={styles.pillRow}>
                    {EATING_GOAL_OPTIONS.map((o) => (
                        <Pill key={o.id} label={o.label} selected={eatingGoal === o.id} onPress={() => setEatingGoal(o.id)} />
                    ))}
                </View>
                <TextInput
                    style={styles.input}
                    value={dietaryRestrictions}
                    onChangeText={setDietaryRestrictions}
                    placeholder="Dietary restrictions (comma-separated)"
                    placeholderTextColor={colors.textMuted}
                />

                <TouchableOpacity style={[styles.primaryBtn, saving && styles.btnDisabled]} onPress={saveProfile} disabled={saving}>
                    <Text style={styles.primaryBtnText}>{saving ? 'Saving...' : 'Generate My Fitmax Plan'}</Text>
                </TouchableOpacity>
            </ScrollView>
        );
    }

    return (
        <View style={styles.container}>
            <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
                <Text style={styles.screenTitle}>Fitmax Dashboard</Text>
                <Text style={styles.subtitle}>
                    {targets?.summary || 'Personalized fitness system powered by your profile.'}
                </Text>

                <View style={styles.statsRow}>
                    <View style={styles.statCard}>
                        <Text style={styles.statValue}>{targets?.calorie_target ?? '-'}</Text>
                        <Text style={styles.statLabel}>Calories</Text>
                    </View>
                    <View style={styles.statCard}>
                        <Text style={styles.statValue}>{targets?.protein_g ?? '-'}</Text>
                        <Text style={styles.statLabel}>Protein (g)</Text>
                    </View>
                    <View style={styles.statCard}>
                        <Text style={styles.statValue}>{weeklyStats.done}/{weeklyStats.target}</Text>
                        <Text style={styles.statLabel}>Workouts</Text>
                    </View>
                </View>

                <View style={styles.progressTrack}>
                    <View style={[styles.progressFill, { width: `${weeklyStats.pct * 100}%` }]} />
                </View>

                <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabRow}>
                    {TABS.map((t) => (
                        <TouchableOpacity
                            key={t.key}
                            style={[styles.tabPill, tab === t.key && styles.tabPillActive]}
                            onPress={() => setTab(t.key)}
                            activeOpacity={0.8}
                        >
                            <Text style={[styles.tabPillText, tab === t.key && styles.tabPillTextActive]}>{t.label}</Text>
                        </TouchableOpacity>
                    ))}
                </ScrollView>

                {tab === 'plan' && (
                    <View style={styles.card}>
                        <View style={styles.cardHeaderRow}>
                            <Text style={styles.cardTitle}>Week Plan</Text>
                            <TouchableOpacity style={styles.ghostBtn} onPress={loadAll}>
                                <Ionicons name="refresh" size={16} color={colors.foreground} />
                                <Text style={styles.ghostBtnText}>Refresh</Text>
                            </TouchableOpacity>
                        </View>
                        {planSessions.map((session: any, idx: number) => (
                            <View key={`${session.day_label}-${idx}`} style={styles.listItem}>
                                <View>
                                    <Text style={styles.itemTitle}>{session.day_label} - {session.focus}</Text>
                                    <Text style={styles.itemSub}>
                                        {session.is_training_day ? `${session.estimated_duration_minutes} min` : 'Recovery day'}
                                    </Text>
                                </View>
                                <Text style={styles.badge}>{session.is_training_day ? 'Train' : 'Rest'}</Text>
                            </View>
                        ))}
                    </View>
                )}

                {tab === 'tracker' && (
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Live Workout Tracker</Text>
                        <Text style={styles.itemSub}>Select session, log reps/weight, and complete.</Text>

                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pillRow}>
                            {trainingSessions.map((s: any, idx: number) => (
                                <Pill
                                    key={`${s.day_label}-${idx}`}
                                    label={`${s.day_label} ${s.focus}`}
                                    selected={selectedSessionIdx === idx}
                                    onPress={() => setSelectedSessionIdx(idx)}
                                />
                            ))}
                        </ScrollView>

                        {selectedSession ? (
                            <>
                                <TouchableOpacity
                                    style={[styles.primaryBtn, { marginTop: spacing.sm }]}
                                    onPress={() => setStartedAt(new Date())}
                                >
                                    <Text style={styles.primaryBtnText}>
                                        {startedAt ? 'Workout Running' : 'Start Workout'}
                                    </Text>
                                </TouchableOpacity>
                                {(selectedSession.exercises || []).map((ex: any, idx: number) => {
                                    const key = `${ex.exercise_id}-${idx}`;
                                    const data = exerciseLogs[key] || { reps: '', weight: '' };
                                    return (
                                        <View key={key} style={styles.exerciseCard}>
                                            <Text style={styles.itemTitle}>{ex.name}</Text>
                                            <Text style={styles.itemSub}>{ex.sets} sets x {ex.reps}</Text>
                                            <View style={styles.row}>
                                                <TextInput
                                                    style={[styles.input, styles.half]}
                                                    placeholder="Reps"
                                                    placeholderTextColor={colors.textMuted}
                                                    keyboardType="number-pad"
                                                    value={data.reps}
                                                    onChangeText={(v) => setExerciseLogs((prev) => ({ ...prev, [key]: { ...data, reps: v } }))}
                                                />
                                                <TextInput
                                                    style={[styles.input, styles.half]}
                                                    placeholder="Weight kg"
                                                    placeholderTextColor={colors.textMuted}
                                                    keyboardType="decimal-pad"
                                                    value={data.weight}
                                                    onChangeText={(v) => setExerciseLogs((prev) => ({ ...prev, [key]: { ...data, weight: v } }))}
                                                />
                                            </View>
                                        </View>
                                    );
                                })}
                                <TouchableOpacity
                                    style={[styles.primaryBtn, !startedAt && styles.btnDisabled]}
                                    disabled={!startedAt}
                                    onPress={completeWorkout}
                                >
                                    <Text style={styles.primaryBtnText}>Complete Session</Text>
                                </TouchableOpacity>
                            </>
                        ) : (
                            <Text style={styles.itemSub}>No training session available.</Text>
                        )}
                    </View>
                )}

                {tab === 'nutrition' && (
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Calorie & Macro Tracker</Text>
                        <View style={styles.statsRow}>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>{nutritionDay?.consumed?.calories || 0}</Text>
                                <Text style={styles.statLabel}>Consumed</Text>
                            </View>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>{targets?.calorie_target || 0}</Text>
                                <Text style={styles.statLabel}>Target</Text>
                            </View>
                            <View style={styles.statCard}>
                                <Text style={styles.statValue}>{Math.max(0, (targets?.calorie_target || 0) - (nutritionDay?.consumed?.calories || 0))}</Text>
                                <Text style={styles.statLabel}>Remaining</Text>
                            </View>
                        </View>

                        <TextInput style={styles.input} value={mealName} onChangeText={setMealName} placeholder="Meal name" placeholderTextColor={colors.textMuted} />
                        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.pillRow}>
                            {['breakfast', 'lunch', 'dinner', 'snacks'].map((t) => (
                                <Pill key={t} label={t} selected={mealType === t} onPress={() => setMealType(t as any)} />
                            ))}
                        </ScrollView>
                        <View style={styles.row}>
                            <TextInput style={[styles.input, styles.half]} value={mealCalories} onChangeText={setMealCalories} placeholder="Calories" placeholderTextColor={colors.textMuted} keyboardType="number-pad" />
                            <TextInput style={[styles.input, styles.half]} value={mealProtein} onChangeText={setMealProtein} placeholder="Protein g" placeholderTextColor={colors.textMuted} keyboardType="number-pad" />
                        </View>
                        <View style={styles.row}>
                            <TextInput style={[styles.input, styles.half]} value={mealCarbs} onChangeText={setMealCarbs} placeholder="Carbs g" placeholderTextColor={colors.textMuted} keyboardType="number-pad" />
                            <TextInput style={[styles.input, styles.half]} value={mealFats} onChangeText={setMealFats} placeholder="Fats g" placeholderTextColor={colors.textMuted} keyboardType="number-pad" />
                        </View>
                        <TouchableOpacity style={styles.primaryBtn} onPress={logMeal}>
                            <Text style={styles.primaryBtnText}>Log Meal</Text>
                        </TouchableOpacity>
                    </View>
                )}

                {tab === 'progress' && (
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Progress Tracker</Text>
                        <Text style={styles.itemSub}>Weekly measurements + performance timeline.</Text>
                        <View style={styles.row}>
                            <TextInput style={[styles.input, styles.half]} value={measurementWeight} onChangeText={setMeasurementWeight} placeholder="Weight kg" placeholderTextColor={colors.textMuted} keyboardType="decimal-pad" />
                            <TextInput style={[styles.input, styles.half]} value={measurementWaist} onChangeText={setMeasurementWaist} placeholder="Waist cm" placeholderTextColor={colors.textMuted} keyboardType="decimal-pad" />
                        </View>
                        <TextInput style={styles.input} value={measurementChest} onChangeText={setMeasurementChest} placeholder="Chest cm" placeholderTextColor={colors.textMuted} keyboardType="decimal-pad" />
                        <TouchableOpacity style={styles.primaryBtn} onPress={logMeasurement}>
                            <Text style={styles.primaryBtnText}>Save Measurement</Text>
                        </TouchableOpacity>

                        <Text style={[styles.label, { marginTop: spacing.lg }]}>Recent Measurements</Text>
                        {(progress?.measurements || []).slice(-6).map((m: any) => (
                            <View key={m.id} style={styles.listItem}>
                                <View>
                                    <Text style={styles.itemTitle}>{new Date(m.measured_on).toLocaleDateString()}</Text>
                                    <Text style={styles.itemSub}>Weight: {m.weight_kg ?? '-'} | Waist: {m.waist_cm ?? '-'}</Text>
                                </View>
                            </View>
                        ))}
                    </View>
                )}

                {tab === 'course' && (
                    <View style={styles.card}>
                        <Text style={styles.cardTitle}>Fitmax Course</Text>
                        <Text style={styles.itemSub}>15 modules, phase-based progression, personalized by your profile.</Text>
                        {(modules || []).map((m: any) => (
                            <View key={m.id || `${m.module_number}`} style={styles.moduleCard}>
                                <Text style={styles.modulePhase}>{m.phase} - Module {m.module_number}</Text>
                                <Text style={styles.itemTitle}>{m.title}</Text>
                                <Text style={styles.itemSub}>{m.description}</Text>
                                {(m.steps || []).slice(0, 3).map((s: any, idx: number) => (
                                    <Text key={`${m.id}-${idx}`} style={styles.stepText}>- {s.title}</Text>
                                ))}
                            </View>
                        ))}
                    </View>
                )}
            </ScrollView>
        </View>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    center: { justifyContent: 'center', alignItems: 'center' },
    content: { padding: spacing.lg, paddingTop: 64, paddingBottom: spacing.xxxl },
    screenTitle: { ...typography.h1, fontSize: 30, marginBottom: spacing.xs },
    subtitle: { ...typography.bodySmall, color: colors.textSecondary, marginBottom: spacing.lg },
    label: { ...typography.label, marginBottom: spacing.sm, marginTop: spacing.md },
    row: { flexDirection: 'row', gap: spacing.sm },
    half: { flex: 1 },
    input: {
        backgroundColor: colors.card,
        borderColor: colors.border,
        borderWidth: 1,
        borderRadius: borderRadius.md,
        paddingHorizontal: spacing.md,
        paddingVertical: 12,
        color: colors.foreground,
        marginBottom: spacing.sm,
    },
    pillRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.xs, marginBottom: spacing.sm },
    pill: {
        paddingHorizontal: spacing.md,
        paddingVertical: 10,
        borderRadius: borderRadius.full,
        borderWidth: 1,
        borderColor: colors.border,
        backgroundColor: colors.card,
    },
    pillSelected: { backgroundColor: colors.foreground, borderColor: colors.foreground },
    pillText: { fontSize: 12, color: colors.textSecondary, fontWeight: '500' },
    pillTextSelected: { color: colors.buttonText, fontWeight: '700' },
    primaryBtn: {
        backgroundColor: colors.foreground,
        borderRadius: borderRadius.full,
        paddingVertical: 14,
        alignItems: 'center',
        marginTop: spacing.sm,
        ...shadows.sm,
    },
    primaryBtnText: { color: colors.buttonText, fontWeight: '700', fontSize: 14 },
    btnDisabled: { opacity: 0.45 },
    statsRow: { flexDirection: 'row', gap: spacing.sm, marginBottom: spacing.sm },
    statCard: {
        flex: 1,
        backgroundColor: colors.card,
        borderRadius: borderRadius.lg,
        padding: spacing.md,
        borderWidth: 1,
        borderColor: colors.border,
    },
    statValue: { fontSize: 20, fontWeight: '700', color: colors.foreground },
    statLabel: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    progressTrack: {
        height: 8,
        borderRadius: 4,
        backgroundColor: colors.borderLight,
        overflow: 'hidden',
        marginBottom: spacing.md,
    },
    progressFill: { height: '100%', backgroundColor: colors.foreground },
    tabRow: { gap: spacing.xs, paddingBottom: spacing.sm },
    tabPill: {
        paddingHorizontal: spacing.md,
        paddingVertical: 8,
        borderRadius: borderRadius.full,
        borderWidth: 1,
        borderColor: colors.border,
        backgroundColor: colors.card,
    },
    tabPillActive: { backgroundColor: colors.foreground, borderColor: colors.foreground },
    tabPillText: { fontSize: 12, color: colors.textSecondary, fontWeight: '600' },
    tabPillTextActive: { color: colors.buttonText },
    card: {
        backgroundColor: colors.card,
        borderRadius: borderRadius.xl,
        padding: spacing.lg,
        borderWidth: 1,
        borderColor: colors.border,
        marginBottom: spacing.md,
        ...shadows.sm,
    },
    cardHeaderRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: spacing.sm },
    cardTitle: { ...typography.h3, fontSize: 18, marginBottom: spacing.sm },
    listItem: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottomWidth: 1,
        borderBottomColor: colors.borderLight,
        paddingVertical: spacing.sm,
    },
    itemTitle: { fontSize: 14, fontWeight: '600', color: colors.foreground },
    itemSub: { fontSize: 12, color: colors.textMuted, marginTop: 2 },
    badge: {
        fontSize: 11,
        color: colors.textSecondary,
        backgroundColor: colors.surface,
        borderRadius: 999,
        paddingHorizontal: 8,
        paddingVertical: 4,
    },
    ghostBtn: {
        flexDirection: 'row',
        alignItems: 'center',
        gap: 4,
        paddingHorizontal: 10,
        paddingVertical: 6,
        borderRadius: borderRadius.full,
        borderWidth: 1,
        borderColor: colors.border,
    },
    ghostBtnText: { fontSize: 12, color: colors.foreground, fontWeight: '600' },
    exerciseCard: {
        backgroundColor: colors.background,
        borderRadius: borderRadius.lg,
        padding: spacing.md,
        marginTop: spacing.sm,
        borderWidth: 1,
        borderColor: colors.borderLight,
    },
    moduleCard: {
        backgroundColor: colors.background,
        borderRadius: borderRadius.lg,
        padding: spacing.md,
        borderWidth: 1,
        borderColor: colors.borderLight,
        marginBottom: spacing.sm,
    },
    modulePhase: { fontSize: 11, color: colors.textMuted, marginBottom: 4, textTransform: 'uppercase' },
    stepText: { fontSize: 12, color: colors.textSecondary, marginTop: 4 },
});
