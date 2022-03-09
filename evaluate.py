import torch
import numpy as np
import matplotlib.pyplot as plt

from backup.evaluate import get_hottest_point


# Get the predicted landmark point from the coordinate of the hottest point
# Heatmap is a tensor of size (B, N, W, H)
def get_hottest_points(output_stack):
    _, _, w, h = output_stack.size()
    flattened_heatmaps = torch.flatten(output_stack, start_dim=2)
    hottest_indices = torch.argmax(flattened_heatmaps, dim=2)
    x = torch.div(hottest_indices, h, rounding_mode="floor")
    y = torch.remainder(hottest_indices, h)
    return torch.stack((y, x), dim=2)


# Heatmap is a tensor of size (B, N, W, H)
def get_eres(output_stack, predicted_points_scaled, pixel_sizes, significant_pixel_cutoff=0.05):
    # flip points
    predicted_points_scaled = torch.flip(predicted_points_scaled, dims=[2])

    flattened_heatmaps = torch.flatten(output_stack, start_dim=2)
    max_per_heatmap, _ = torch.max(flattened_heatmaps, dim=2, keepdim=True)
    max_per_heatmap = torch.unsqueeze(max_per_heatmap, dim=3)
    normalized_heatmaps = torch.div(output_stack, max_per_heatmap)

    filtered_heatmaps = torch.where(normalized_heatmaps > significant_pixel_cutoff, normalized_heatmaps,
                                   torch.tensor(0.0).cuda())
    flattened_filtered_heatmaps = torch.flatten(filtered_heatmaps, start_dim=2)
    sum_per_heatmap = torch.sum(flattened_filtered_heatmaps, dim=2, keepdim=True)
    sum_per_heatmap = torch.unsqueeze(sum_per_heatmap, dim=3)
    pdfs = torch.div(filtered_heatmaps, sum_per_heatmap)
    eres_per_image = []
    for heatmap_stack, predicted_points_per_image, pixel_size in zip(pdfs, predicted_points_scaled, pixel_sizes):
        ere_per_heatmap = []
        for pdf, predicted_point in zip(heatmap_stack, predicted_points_per_image):
            indices = torch.nonzero(pdf)

            pdf_flattened = torch.flatten(pdf)
            flattened_indices = torch.nonzero(pdf_flattened)
            significant_values = pdf_flattened[flattened_indices]

            scaled_indices = torch.multiply(indices, pixel_size)
            displacement_vectors = torch.sub(scaled_indices, predicted_point)
            distances = torch.norm(displacement_vectors, dim=1)
            ere = torch.sum(torch.multiply(torch.squeeze(significant_values), distances))
            ere_per_heatmap.append(ere)
        eres_per_image.append(torch.stack(ere_per_heatmap))

    return torch.stack(eres_per_image)


def get_predicted_and_target_points(output_stack, landmarks_per_annotator, pixels_sizes):
    # Evaluate radial error
    # Predicted points has shape (B, N, 2)
    predicted_points = get_hottest_points(output_stack)
    scaled_predicted_points = torch.multiply(predicted_points, pixels_sizes)

    # Average the landmarks per annotator
    target_points = torch.mean(landmarks_per_annotator, dim=1)
    scaled_target_points = torch.multiply(target_points, pixels_sizes)

    # Get expected radial error scores
    eres = get_eres(output_stack, scaled_predicted_points, pixels_sizes)

    return scaled_predicted_points, scaled_target_points, eres


def cal_radial_errors(predicted_points, target_points, mean=False):
    '''

    :param predicted_points: tensor of size [D, N, 2]
    :param target_points: tensor of size [D, N, 2]
    :return: the distance between each point, a tensor of size [D, N]
    '''

    displacement = predicted_points - target_points
    per_landmark_error = torch.norm(displacement, dim=2)
    if mean:
        return torch.mean(per_landmark_error).item()
    else:
        return per_landmark_error


def get_confidence_weighted_points(predicted_points_per_model, eres_per_model):
    '''

    :param predicted_points_per_model: tensor of size [M, D, N, 2]
    :param eres_per_model: tensor of size [M, D, N]
    :return: a tensor of size [D, N, 2] representing the confidence weighted points
    '''

    inverted_eres = torch.reciprocal(eres_per_model)
    # make inverted_eres size [M, D, N, 1] so it can be multiplied
    weighted_points = torch.multiply(predicted_points_per_model, torch.unsqueeze(inverted_eres, -1))
    # weighted points has size [M, D, N, 2]
    average_points = torch.mean(weighted_points, dim=0)
    # average points has size [D, N, 2]
    total_inverted_eres = torch.sum(inverted_eres, dim=0)
    # total_inverted_eres has size [D, N]
    return torch.divide(average_points, torch.unsqueeze(total_inverted_eres, -1))


def get_sdr_statistics(radial_errors, thresholds):
    successful_detection_rates = []
    for threshold in thresholds:
        filter = torch.where(radial_errors < threshold, 1.0, 0.0)
        sdr = 100 * torch.sum(filter) / torch.numel(radial_errors)
        successful_detection_rates.append(sdr)
    return successful_detection_rates
