/**
 * Scan Detail Screen - Full analysis for a specific scan
 */

import React, { useEffect, useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, ActivityIndicator } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { Ionicons } from '@expo/vector-icons';
import api from '../../services/api';
import { colors, spacing, borderRadius, typography } from '../../theme/dark';

export default function ScanDetailScreen() {
    const navigation = useNavigation<any>();
    const route = useRoute<any>();
    const { scanId } = route.params;
    const [scan, setScan] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadScan();
    }, []);

    const loadScan = async () => {
        try {
            const result = await api.getScanById(scanId);
            setScan(result);
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const safeToFixed = (val: any, digits: number = 1): string => {
        const num = parseFloat(val);
        return isNaN(num) ? '0.0' : num.toFixed(digits);
    };

    const getScoreColor = (score: number) => {
        const s = parseFloat(String(score)) || 0;
        if (s >= 7) return colors.success;
        if (s >= 5) return colors.warning;
        return colors.error;
    };

    const a = scan?.analysis || {};
    const overallScore = parseFloat(a.scan_summary?.overall_score) || parseFloat(a.metrics?.overall_score) || parseFloat(a.overall_score) || 0;

    let recommendations: any[] = [];
    if (a.ai_recommendations?.recommendations) {
        recommendations = a.ai_recommendations.recommendations.map((r: any) => ({
            area: r.title || 'General',
            suggestion: r.description || r.suggestion || ''
        }));
    } else {
        recommendations = a.improvements || a.recommendations || [];
    }

    const getMetricValue = (key: string): number => {
        // Try new format first
        if (a.measurements) {
            const f = a.measurements.front_view || {};
            const p = a.measurements.profile_view || {};
            switch (key) {
                case 'midface_ratio': return f.midface_ratio?.score ?? 0;
                case 'canthal_tilt': return f.canthal_tilt_left?.score ?? 0;
                case 'jaw_cheek_ratio': return f.jaw_cheek_ratio?.score ?? 0;
                case 'nose_width_ratio': return f.nose_width_ratio?.score ?? 0;
                case 'gonial_angle': return p.gonial_angle?.score ?? 0;
                case 'nasolabial_angle': return p.nasolabial_angle?.score ?? 0;
                case 'mentolabial_angle': return p.mentolabial_angle?.score ?? 0;
                case 'facial_convexity': return p.facial_convexity?.score ?? 0;
            }
        }

        // Fallback to old format
        const m = a.metrics || a;
        switch (key) {
            case 'facial_symmetry': return m.proportions?.overall_symmetry ?? m.harmony_score ?? 0;
            case 'jawline_definition': return m.jawline?.definition_score ?? 0;
            case 'skin_quality': return m.skin?.overall_quality ?? 0;
            case 'facial_fat': return m.body_fat?.facial_leanness ?? 0;
            case 'eye_area': return m.eye_area?.symmetry_score ?? 0;
            case 'nose_proportion': return m.nose?.overall_harmony ?? 0;
            case 'lip_ratio': return m.lips?.lip_symmetry ?? 0;
            default: return 0;
        }
    };

    const getMetricDetails = (key: string): { value: number; actualValue?: number; rating?: string } => {
        if (a.measurements) {
            const f = a.measurements.front_view || {};
            const p = a.measurements.profile_view || {};
            
            switch (key) {
                case 'midface_ratio': 
                    return { 
                        value: f.midface_ratio?.score ?? 0, 
                        actualValue: f.midface_ratio?.value, 
                        rating: f.midface_ratio?.rating 
                    };
                case 'canthal_tilt_left': 
                    return { 
                        value: f.canthal_tilt_left?.score ?? 0, 
                        actualValue: f.canthal_tilt_left?.value, 
                        rating: f.canthal_tilt_left?.rating 
                    };
                case 'canthal_tilt_right': 
                    return { 
                        value: f.canthal_tilt_right?.score ?? 0, 
                        actualValue: f.canthal_tilt_right?.value, 
                        rating: f.canthal_tilt_right?.rating 
                    };
                case 'symmetry_score': 
                    return { value: f.symmetry_score?.value ?? 0 };
                case 'jaw_cheek_ratio': 
                    return { 
                        value: f.jaw_cheek_ratio?.score ?? 0, 
                        actualValue: f.jaw_cheek_ratio?.value, 
                        rating: f.jaw_cheek_ratio?.rating 
                    };
                case 'nose_width_ratio': 
                    return { 
                        value: f.nose_width_ratio?.score ?? 0, 
                        actualValue: f.nose_width_ratio?.value, 
                        rating: f.nose_width_ratio?.rating 
                    };
                case 'face_width_height_ratio': 
                    return { value: f.face_width_height_ratio?.value ?? 0 };
                case 'philtrum_length_mm': 
                    return { value: f.philtrum_length_mm?.value ?? 0 };
                case 'ipd_mm': 
                    return { value: f.ipd_mm?.value ?? 0 };
                case 'esr': 
                    return { value: f.esr?.value ?? 0 };
                case 'gonial_angle': 
                    return { 
                        value: p.gonial_angle?.score ?? 0, 
                        actualValue: p.gonial_angle?.value, 
                        rating: p.gonial_angle?.rating 
                    };
                case 'nasolabial_angle': 
                    return { 
                        value: p.nasolabial_angle?.score ?? 0, 
                        actualValue: p.nasolabial_angle?.value, 
                        rating: p.nasolabial_angle?.rating 
                    };
                case 'mentolabial_angle': 
                    return { 
                        value: p.mentolabial_angle?.score ?? 0, 
                        actualValue: p.mentolabial_angle?.value, 
                        rating: p.mentolabial_angle?.rating 
                    };
                case 'facial_convexity': 
                    return { 
                        value: p.facial_convexity?.score ?? 0, 
                        actualValue: p.facial_convexity?.value, 
                        rating: p.facial_convexity?.rating 
                    };
                case 'chin_projection': 
                    return { value: p.chin_projection?.value ?? 0 };
            }
        }
        return { value: 0 };
    };

    const metricItems = a.measurements ? [
        // Front View Measurements
        { key: 'midface_ratio', label: 'Midface Ratio', icon: 'resize', section: 'Front View' },
        { key: 'canthal_tilt_left', label: 'Canthal Tilt (Left)', icon: 'eye', section: 'Front View' },
        { key: 'canthal_tilt_right', label: 'Canthal Tilt (Right)', icon: 'eye', section: 'Front View' },
        { key: 'symmetry_score', label: 'Symmetry Score', icon: 'grid', section: 'Front View' },
        { key: 'jaw_cheek_ratio', label: 'Jaw-Cheek Ratio', icon: 'fitness', section: 'Front View' },
        { key: 'nose_width_ratio', label: 'Nose Width Ratio', icon: 'water', section: 'Front View' },
        { key: 'face_width_height_ratio', label: 'Face Width/Height Ratio', icon: 'resize', section: 'Front View' },
        { key: 'philtrum_length_mm', label: 'Philtrum Length (mm)', icon: 'body', section: 'Front View' },
        { key: 'ipd_mm', label: 'Interpupillary Distance (mm)', icon: 'eye', section: 'Front View' },
        { key: 'esr', label: 'Eye Separation Ratio', icon: 'eye', section: 'Front View' },
        
        // Profile View Measurements
        { key: 'gonial_angle', label: 'Gonial Angle', icon: 'analytics', section: 'Profile View' },
        { key: 'nasolabial_angle', label: 'Nasolabial Angle', icon: 'git-merge', section: 'Profile View' },
        { key: 'mentolabial_angle', label: 'Mentolabial Angle', icon: 'git-commit', section: 'Profile View' },
        { key: 'facial_convexity', label: 'Facial Convexity', icon: 'person', section: 'Profile View' },
        { key: 'chin_projection', label: 'Chin Projection', icon: 'person', section: 'Profile View' },
    ] : [
        { key: 'facial_symmetry', label: 'Facial Symmetry', icon: 'grid', section: 'General' },
        { key: 'jawline_definition', label: 'Jawline Definition', icon: 'fitness', section: 'General' },
        { key: 'skin_quality', label: 'Skin Quality', icon: 'sparkles', section: 'General' },
        { key: 'facial_fat', label: 'Facial Leanness', icon: 'body', section: 'General' },
        { key: 'eye_area', label: 'Eye Area', icon: 'eye', section: 'General' },
        { key: 'nose_proportion', label: 'Nose Harmony', icon: 'resize', section: 'General' },
        { key: 'lip_ratio', label: 'Lip Balance', icon: 'ellipse', section: 'General' },
    ];

    if (loading) {
        return (
            <View style={[styles.container, styles.centerContent]}>
                <ActivityIndicator size="large" color={colors.primary} />
                <Text style={styles.loadingText}>Loading scan...</Text>
            </View>
        );
    }

    if (!scan) {
        return (
            <View style={[styles.container, styles.centerContent]}>
                <Text style={styles.errorText}>Scan not found</Text>
                <TouchableOpacity onPress={() => navigation.goBack()}>
                    <Text style={{ color: colors.primary }}>Go Back</Text>
                </TouchableOpacity>
            </View>
        );
    }

    return (
        <ScrollView style={styles.container} contentContainerStyle={styles.content}>
            <View style={styles.header}>
                <TouchableOpacity onPress={() => navigation.goBack()} style={styles.backButton}>
                    <Ionicons name="arrow-back" size={24} color={colors.textPrimary} />
                </TouchableOpacity>
                <Text style={styles.title}>Scan Details</Text>
                <View style={{ width: 40 }} />
            </View>

            <Text style={styles.dateText}>{new Date(scan.created_at).toLocaleDateString('en-US', {
                weekday: 'long', year: 'numeric', month: 'long', day: 'numeric'
            })}</Text>

            {/* Overall Score Card */}
            <View style={styles.scoreCard}>
                <Text style={styles.scoreLabel}>Overall Score</Text>
                <Text style={[styles.score, { color: getScoreColor(overallScore) }]}>
                    {safeToFixed(overallScore)}
                </Text>
                <Text style={styles.scoreMax}>/10</Text>
            </View>

            {/* Scan Summary Info */}
            {a.scan_summary && (
                <View style={styles.summaryCard}>
                    <Text style={styles.sectionTitle}>Scan Summary</Text>
                    <View style={styles.summaryRow}>
                        <Text style={styles.summaryLabel}>Frames Analyzed:</Text>
                        <Text style={styles.summaryValue}>{a.scan_summary.frames_analyzed || 'N/A'}</Text>
                    </View>
                    {a.scan_summary.frames_by_angle && (
                        <View style={styles.summaryRow}>
                            <Text style={styles.summaryLabel}>Frames by Angle:</Text>
                            <Text style={styles.summaryValue}>
                                Front: {a.scan_summary.frames_by_angle.front || 0}, 
                                Left: {a.scan_summary.frames_by_angle.left_profile || 0}, 
                                Right: {a.scan_summary.frames_by_angle.right_profile || 0}
                            </Text>
                        </View>
                    )}
                </View>
            )}

            {/* Golden Ratio Analysis */}
            {a.golden_ratio_analysis && (
                <View style={styles.goldenRatioCard}>
                    <Text style={styles.sectionTitle}>Golden Ratio Analysis</Text>
                    <View style={styles.summaryRow}>
                        <Text style={styles.summaryLabel}>Average Score:</Text>
                        <Text style={[styles.summaryValue, { color: getScoreColor(a.golden_ratio_analysis.average_score) }]}>
                            {safeToFixed(a.golden_ratio_analysis.average_score)}
                        </Text>
                    </View>
                    {a.golden_ratio_analysis.scores && Object.keys(a.golden_ratio_analysis.scores).length > 0 && (
                        <View style={styles.scoresList}>
                            {Object.entries(a.golden_ratio_analysis.scores).map(([key, score]) => (
                                <View key={key} style={styles.scoreItem}>
                                    <Text style={styles.scoreItemLabel}>{key.replace(/_/g, ' ')}:</Text>
                                    <Text style={[styles.scoreItemValue, { color: getScoreColor(score as number) }]}>
                                        {safeToFixed(score as number)}
                                    </Text>
                                </View>
                            ))}
                        </View>
                    )}
                </View>
            )}

            {/* Detailed Metrics */}
            <Text style={styles.sectionTitle}>Detailed Analysis</Text>
            {(() => {
                const groupedMetrics = metricItems.reduce((acc, item) => {
                    if (!acc[item.section]) acc[item.section] = [];
                    acc[item.section].push(item);
                    return acc;
                }, {} as Record<string, typeof metricItems>);

                return Object.entries(groupedMetrics).map(([section, items]) => (
                    <View key={section} style={styles.metricsCard}>
                        <Text style={styles.subsectionTitle}>{section}</Text>
                        {items.map((item) => {
                            const details = getMetricDetails(item.key);
                            return (
                                <View key={item.key} style={styles.metricItem}>
                                    <View style={styles.metricLeft}>
                                        <Ionicons name={item.icon as any} size={20} color={colors.primary} />
                                        <View style={styles.metricLabelContainer}>
                                            <Text style={styles.metricLabel}>{item.label}</Text>
                                            {details.rating && (
                                                <Text style={[styles.rating, { color: getScoreColor(details.value) }]}>
                                                    {details.rating}
                                                </Text>
                                            )}
                                        </View>
                                    </View>
                                    <View style={styles.metricRight}>
                                        <View style={styles.metricBar}>
                                            <View style={[styles.metricFill, { width: `${Math.min(details.value * 10, 100)}%`, backgroundColor: getScoreColor(details.value) }]} />
                                        </View>
                                        <View style={styles.metricValues}>
                                            <Text style={[styles.metricValue, { color: getScoreColor(details.value) }]}>
                                                {safeToFixed(details.value)}
                                            </Text>
                                            {details.actualValue !== undefined && (
                                                <Text style={styles.actualValue}>
                                                    ({details.actualValue}{item.key.includes('mm') ? 'mm' : item.key.includes('angle') || item.key.includes('gonial') || item.key.includes('nasolabial') || item.key.includes('mentolabial') ? '°' : ''})
                                                </Text>
                                            )}
                                        </View>
                                    </View>
                                </View>
                            );
                        })}
                    </View>
                ));
            })()}

            {/* Recommendations */}
            {recommendations.length > 0 && (
                <>
                    <Text style={styles.sectionTitle}>Recommendations</Text>
                    <View style={styles.recommendationsCard}>
                        {recommendations.map((rec: any, index: number) => (
                            <View key={index} style={styles.recItem}>
                                <Ionicons name="checkmark-circle" size={20} color={colors.primary} />
                                <View style={styles.recContent}>
                                    <Text style={styles.recArea}>{rec.area}</Text>
                                    <Text style={styles.recSuggestion}>{rec.suggestion}</Text>
                                </View>
                            </View>
                        ))}
                    </View>
                </>
            )}
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: { flex: 1, backgroundColor: colors.background },
    centerContent: { justifyContent: 'center', alignItems: 'center' },
    content: { paddingBottom: spacing.xxl },
    header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingTop: 60, paddingHorizontal: spacing.lg, paddingBottom: spacing.md },
    backButton: { width: 40, height: 40, justifyContent: 'center' },
    title: { ...typography.h2 },
    dateText: { ...typography.bodySmall, textAlign: 'center', color: colors.textMuted, marginBottom: spacing.md },
    loadingText: { ...typography.body, marginTop: spacing.md, color: colors.textSecondary },
    errorText: { ...typography.body, color: colors.error, marginBottom: spacing.md },
    scoreCard: { margin: spacing.lg, backgroundColor: colors.surface, borderRadius: borderRadius.lg, padding: spacing.xl, alignItems: 'center' },
    scoreLabel: { ...typography.bodySmall },
    score: { fontSize: 80, fontWeight: '800', lineHeight: 90 },
    scoreMax: { ...typography.h3, color: colors.textMuted },
    sectionTitle: { ...typography.h3, marginHorizontal: spacing.lg, marginTop: spacing.lg, marginBottom: spacing.md },
    summaryCard: { marginHorizontal: spacing.lg, backgroundColor: colors.surface, borderRadius: borderRadius.lg, padding: spacing.lg, marginBottom: spacing.md },
    summaryRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: spacing.sm },
    summaryLabel: { ...typography.bodySmall, color: colors.textSecondary },
    summaryValue: { ...typography.body, fontWeight: '600' },
    goldenRatioCard: { marginHorizontal: spacing.lg, backgroundColor: colors.surface, borderRadius: borderRadius.lg, padding: spacing.lg, marginBottom: spacing.md },
    scoresList: { marginTop: spacing.md },
    scoreItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: spacing.xs, borderBottomWidth: 1, borderBottomColor: colors.border },
    scoreItemLabel: { ...typography.bodySmall, color: colors.textSecondary },
    scoreItemValue: { ...typography.body, fontWeight: '600' },
    metricsCard: { marginHorizontal: spacing.lg, backgroundColor: colors.surface, borderRadius: borderRadius.lg, padding: spacing.lg, marginBottom: spacing.md },
    subsectionTitle: { ...typography.h3, marginBottom: spacing.md, color: colors.primary, fontSize: 16 },
    metricItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: spacing.sm, borderBottomWidth: 1, borderBottomColor: colors.border },
    metricLeft: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm, flex: 1 },
    metricLabelContainer: { flex: 1 },
    metricLabel: { ...typography.bodySmall },
    rating: { ...typography.bodySmall, fontStyle: 'italic', marginTop: 2 },
    metricRight: { flexDirection: 'row', alignItems: 'center', gap: spacing.md, flex: 1 },
    metricBar: { flex: 1, height: 8, backgroundColor: colors.border, borderRadius: 4, maxWidth: 100 },
    metricFill: { height: '100%', borderRadius: 4, maxWidth: '100%' },
    metricValues: { alignItems: 'flex-end' },
    metricValue: { ...typography.body, fontWeight: '700', width: 35, textAlign: 'right' },
    actualValue: { ...typography.bodySmall, color: colors.textMuted, textAlign: 'right' },
    recommendationsCard: { marginHorizontal: spacing.lg, backgroundColor: colors.surface, borderRadius: borderRadius.lg, padding: spacing.lg, gap: spacing.md },
    recItem: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing.md },
    recContent: { flex: 1 },
    recArea: { ...typography.body, fontWeight: '600' },
    recSuggestion: { ...typography.bodySmall, marginTop: 2 },
});
