import React, { useState, useEffect } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ScrollView, Alert, TextInput, KeyboardAvoidingView, Platform, ActivityIndicator } from 'react-native';
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

export default function EditPersonalScreen() {
  const navigation = useNavigation<any>();
  const { user, refreshUser } = useAuth();
  const [loading, setLoading] = useState(false);

  // Initial Unit System
  const [unitSystem, setUnitSystem] = useState<'metric' | 'imperial'>((user?.onboarding?.unit_system as any) || 'metric');

  // Form State
  const [selectedGoals, setSelectedGoals] = useState<string[]>(user?.onboarding?.goals || []);
  const [gender, setGender] = useState(user?.onboarding?.gender || '');
  const [age, setAge] = useState(user?.onboarding?.age?.toString() || '');

  // Height & Weight handling
  const getInitialValues = () => {
    let h = '', hFt = '', hIn = '', w = '';
    const ob = user?.onboarding;
    if (ob) {
      if (unitSystem === 'imperial') {
        w = ob.weight ? (ob.weight * 2.20462).toFixed(1) : '';
        if (ob.height) {
          const totalInches = ob.height / 2.54;
          hFt = Math.floor(totalInches / 12).toString();
          hIn = Math.round(totalInches % 12).toString();
        }
      } else {
        h = ob.height?.toString() || '';
        w = ob.weight?.toString() || '';
      }
    }
    return { h, hFt, hIn, w };
  };

  const initial = getInitialValues();
  const [height, setHeight] = useState(initial.h);
  const [heightFt, setHeightFt] = useState(initial.hFt);
  const [heightIn, setHeightIn] = useState(initial.hIn);
  const [weight, setWeight] = useState(initial.w);

  const [activityLevel, setActivityLevel] = useState(user?.onboarding?.activity_level || '');
  const [selectedEquipment, setSelectedEquipment] = useState<string[]>(user?.onboarding?.equipment || []);
  const [experience, setExperience] = useState(user?.onboarding?.experience_level || '');
  const [skinType, setSkinType] = useState(user?.onboarding?.skin_type || '');

  const handleSave = async () => {
    if (selectedGoals.length === 0 || !gender || !age || !weight || !activityLevel || selectedEquipment.length === 0 || !experience || !skinType) {
      Alert.alert('Required', 'Please fill in all mandatory fields');
      return;
    }

    setLoading(true);

    let finalHeight = parseFloat(height);
    let finalWeight = parseFloat(weight);

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
        timezone: user?.onboarding?.timezone || (typeof Intl !== 'undefined' ? Intl.DateTimeFormat().resolvedOptions().timeZone : 'UTC'),
        completed: true
      });
      await refreshUser();
      Alert.alert('Success', 'Profile updated successfully!');
      navigation.goBack();
    } catch (error) {
      Alert.alert('Error', 'Could not save changes. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color={colors.foreground} />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Edit Personal Info</Text>
        <TouchableOpacity onPress={handleSave} disabled={loading} style={styles.saveHeaderBtn}>
          {loading ? <ActivityIndicator size="small" color={colors.accent} /> : <Text style={styles.saveHeaderText}>Save</Text>}
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} style={{ flex: 1 }}>
        <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>

          {/* Goals Section */}
          <Text style={styles.sectionTitle}>Your Goals</Text>
          <View style={styles.goalsGrid}>
            {GOALS.map((goal) => {
              const selected = selectedGoals.includes(goal.id);
              return (
                <TouchableOpacity
                  key={goal.id}
                  style={[styles.goalCard, selected && styles.goalCardSelected]}
                  onPress={() => setSelectedGoals(prev => prev.includes(goal.id) ? prev.filter(g => g !== goal.id) : [...prev, goal.id])}
                >
                  <Ionicons name={goal.icon as any} size={20} color={selected ? colors.foreground : colors.textMuted} />
                  <Text style={[styles.goalLabel, selected && styles.goalLabelSelected]}>{goal.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Physical Section */}
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Physical Profile</Text>
            <View style={styles.unitToggle}>
              <TouchableOpacity onPress={() => setUnitSystem('metric')} style={[styles.unitBtn, unitSystem === 'metric' && styles.unitBtnActive]}>
                <Text style={[styles.unitLabel, unitSystem === 'metric' && styles.unitLabelActive]}>Metric</Text>
              </TouchableOpacity>
              <TouchableOpacity onPress={() => setUnitSystem('imperial')} style={[styles.unitBtn, unitSystem === 'imperial' && styles.unitBtnActive]}>
                <Text style={[styles.unitLabel, unitSystem === 'imperial' && styles.unitLabelActive]}>US</Text>
              </TouchableOpacity>
            </View>
          </View>

          <Text style={styles.inputLabel}>GENDER</Text>
          <View style={styles.chipRow}>
            {['Male', 'Female', 'Other'].map(g => (
              <TouchableOpacity key={g} style={[styles.chip, gender === g && styles.chipSelected]} onPress={() => setGender(g)}>
                <Text style={[styles.chipText, gender === g && styles.chipTextSelected]}>{g}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={styles.inputGroup}>
            <View style={styles.inputHalf}>
              <Text style={styles.inputLabel}>AGE</Text>
              <TextInput style={styles.input} keyboardType="numeric" value={age} onChangeText={setAge} placeholder="Years" placeholderTextColor={colors.textMuted} />
            </View>
            <View style={styles.inputHalf}>
              <Text style={styles.inputLabel}>WEIGHT ({unitSystem === 'metric' ? 'KG' : 'LBS'})</Text>
              <TextInput style={styles.input} keyboardType="numeric" value={weight} onChangeText={setWeight} placeholder={unitSystem === 'metric' ? "kg" : "lbs"} placeholderTextColor={colors.textMuted} />
            </View>
          </View>

          <Text style={styles.inputLabel}>HEIGHT ({unitSystem === 'metric' ? 'CM' : 'FT/IN'})</Text>
          {unitSystem === 'metric' ? (
            <TextInput style={styles.input} keyboardType="numeric" value={height} onChangeText={setHeight} placeholder="cm" placeholderTextColor={colors.textMuted} />
          ) : (
            <View style={styles.inputGroup}>
              <View style={styles.inputHalf}><TextInput style={styles.input} keyboardType="numeric" value={heightFt} onChangeText={setHeightFt} placeholder="ft" placeholderTextColor={colors.textMuted} /></View>
              <View style={styles.inputHalf}><TextInput style={styles.input} keyboardType="numeric" value={heightIn} onChangeText={setHeightIn} placeholder="in" placeholderTextColor={colors.textMuted} /></View>
            </View>
          )}

          {/* Lifestyle Section */}
          <Text style={[styles.sectionTitle, { marginTop: spacing.xl }]}>Lifestyle</Text>

          <Text style={styles.inputLabel}>ACTIVITY LEVEL</Text>
          <View style={styles.list}>
            {ACTIVITY_LEVELS.map(level => (
              <TouchableOpacity key={level.id} style={[styles.listCard, activityLevel === level.id && styles.listCardSelected]} onPress={() => setActivityLevel(level.id)}>
                <View>
                  <Text style={styles.listLabel}>{level.label}</Text>
                  <Text style={styles.listDesc}>{level.desc}</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={[styles.inputLabel, { marginTop: spacing.lg }]}>EQUIPMENT ACCESS</Text>
          <View style={styles.chipRow}>
            {EQUIPMENT.map(item => {
              const selected = selectedEquipment.includes(item.id);
              return (
                <TouchableOpacity
                  key={item.id}
                  style={[styles.chip, selected && styles.chipSelected]}
                  onPress={() => setSelectedEquipment(prev => prev.includes(item.id) ? prev.filter(i => i !== item.id) : [...prev, item.id])}
                >
                  <Text style={[styles.chipText, selected && styles.chipTextSelected]}>{item.label}</Text>
                </TouchableOpacity>
              );
            })}
          </View>

          {/* Last Details */}
          <Text style={[styles.sectionTitle, { marginTop: spacing.xl }]}>Experience & Skin</Text>

          <Text style={styles.inputLabel}>EXPERIENCE LEVEL</Text>
          <View style={styles.list}>
            {EXPERIENCE.map(exp => (
              <TouchableOpacity key={exp.id} style={[styles.listCard, experience === exp.id && styles.listCardSelected]} onPress={() => setExperience(exp.id)}>
                <View>
                  <Text style={styles.listLabel}>{exp.label}</Text>
                  <Text style={styles.listDesc}>{exp.desc}</Text>
                </View>
              </TouchableOpacity>
            ))}
          </View>

          <Text style={[styles.inputLabel, { marginTop: spacing.lg }]}>SKIN TYPE</Text>
          <View style={styles.chipRow}>
            {SKIN_TYPES.map(type => (
              <TouchableOpacity key={type.id} style={[styles.chip, skinType === type.id && styles.chipSelected]} onPress={() => setSkinType(type.id)}>
                <Text style={[styles.chipText, skinType === type.id && styles.chipTextSelected]}>{type.label}</Text>
              </TouchableOpacity>
            ))}
          </View>

          <View style={{ height: 100 }} />
        </ScrollView>
      </KeyboardAvoidingView>

      <View style={styles.footer}>
        <TouchableOpacity style={[styles.saveBtn, loading && { opacity: 0.7 }]} onPress={handleSave} disabled={loading}>
          <Text style={styles.saveBtnText}>{loading ? 'Saving...' : 'Save All Changes'}</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  header: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingTop: 60, paddingHorizontal: spacing.lg, paddingBottom: spacing.md,
    borderBottomWidth: 1, borderBottomColor: colors.borderLight
  },
  headerTitle: { ...typography.h3, color: colors.foreground },
  backButton: { padding: 4 },
  saveHeaderBtn: { padding: 4 },
  saveHeaderText: { fontSize: 16, fontWeight: '600', color: colors.accent },
  content: { padding: spacing.lg },
  sectionTitle: { ...typography.h2, fontSize: 20, marginBottom: spacing.md, marginTop: spacing.md },
  sectionHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginTop: spacing.xl, marginBottom: spacing.sm },
  goalsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  goalCard: {
    width: '31%', backgroundColor: colors.card, borderRadius: borderRadius.lg,
    padding: spacing.md, alignItems: 'center', justifyContent: 'center',
    borderWidth: 1, borderColor: 'transparent', ...shadows.sm,
  },
  goalCardSelected: { backgroundColor: colors.accentMuted, borderColor: colors.foreground },
  goalLabel: { ...typography.caption, marginTop: spacing.xs, color: colors.textSecondary, textAlign: 'center' },
  goalLabelSelected: { color: colors.foreground, fontWeight: '600' },
  unitToggle: {
    flexDirection: 'row', backgroundColor: colors.card, borderRadius: borderRadius.full,
    padding: 4, borderWidth: 1, borderColor: colors.borderLight,
  },
  unitBtn: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: borderRadius.full },
  unitBtnActive: { backgroundColor: colors.foreground },
  unitLabel: { fontSize: 12, fontWeight: '600', color: colors.textMuted },
  unitLabelActive: { color: colors.background },
  inputLabel: { ...typography.label, color: colors.textMuted, marginBottom: spacing.sm, marginTop: spacing.md },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing.sm },
  chip: {
    paddingHorizontal: 16, paddingVertical: 8, borderRadius: borderRadius.full,
    backgroundColor: colors.card, borderWidth: 1, borderColor: colors.borderLight,
  },
  chipSelected: { backgroundColor: colors.foreground, borderColor: colors.foreground },
  chipText: { ...typography.bodySmall, color: colors.textSecondary },
  chipTextSelected: { color: colors.background, fontWeight: '600' },
  inputGroup: { flexDirection: 'row', gap: spacing.md },
  inputHalf: { flex: 1 },
  input: {
    backgroundColor: colors.card, borderRadius: borderRadius.md, padding: 16,
    color: colors.foreground, fontSize: 16, borderWidth: 1, borderColor: colors.borderLight,
  },
  list: { gap: spacing.sm },
  listCard: {
    backgroundColor: colors.card, borderRadius: borderRadius.lg, padding: 16,
    borderWidth: 1, borderColor: 'transparent',
  },
  listCardSelected: { backgroundColor: colors.accentMuted, borderColor: colors.foreground },
  listLabel: { ...typography.body, fontWeight: '600', color: colors.foreground },
  listDesc: { ...typography.caption, color: colors.textMuted, marginTop: 2 },
  footer: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    padding: spacing.lg, paddingBottom: Platform.OS === 'ios' ? 40 : 20,
    backgroundColor: colors.background, borderTopWidth: 1, borderTopColor: colors.borderLight,
  },
  saveBtn: {
    backgroundColor: colors.foreground, borderRadius: borderRadius.full,
    paddingVertical: 18, alignItems: 'center', ...shadows.md,
  },
  saveBtnText: { ...typography.button, color: colors.background },
});
